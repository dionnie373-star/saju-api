"""주문 멱등성 기록 / Digistore24 보류 주문 저장소.

DATABASE_URL 환경변수가 설정되면 Postgres에 영구 저장하고, 설정 안 되어
있으면 기존과 똑같은 메모리(dict/set) 방식으로 동작한다 — 즉 DATABASE_URL을
아직 안 만든 상태로 배포해도 지금까지와 완전히 동일하게 돌아간다(메모리
기반, 단일 gunicorn 워커 가정, 서버 재시작 시 초기화). 나중에 DATABASE_URL만
추가하면 코드 변경 없이 영구 저장소로 전환된다.

app.py는 이 모듈의 함수만 호출하고 저장 방식(메모리 vs DB)을 몰라도 된다.

필요 패키지: psycopg2-binary (requirements.txt에 추가됨). DATABASE_URL이
설정 안 된 환경(로컬 개발, 테스트)에서는 이 패키지가 없어도 전혀 문제없다 —
_get_conn()은 DATABASE_URL이 있을 때만 호출되고, 그때 비로소 import한다.
"""
import os
import threading
import time

DATABASE_URL = os.environ.get("DATABASE_URL")

# --- 메모리 모드 상태 (DATABASE_URL 미설정 시 사용) --------------------------
_MEM_PROCESSED = set()  # {(provider, order_id)}
_MEM_PROCESSED_LOCK = threading.Lock()
_MEM_PROCESSED_MAX = 2000  # 메모리 누수 방지용 상한선 (평소에는 절대 도달하지 않음)

_MEM_PENDING = {}  # token -> {"data": dict, "created_at": float(epoch)}
_MEM_PENDING_LOCK = threading.Lock()

_pg_schema_ready = False
_pg_schema_lock = threading.Lock()


def _use_db() -> bool:
    return bool(DATABASE_URL)


def _get_conn():
    import psycopg2  # DATABASE_URL이 설정된 환경(Render)에서만 import됨

    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    return conn


def _ensure_schema(conn):
    global _pg_schema_ready
    if _pg_schema_ready:
        return
    with _pg_schema_lock:
        if _pg_schema_ready:
            return
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS processed_orders (
                    provider TEXT NOT NULL,
                    order_id TEXT NOT NULL,
                    processed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    PRIMARY KEY (provider, order_id)
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS pending_orders (
                    token TEXT PRIMARY KEY,
                    data JSONB NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
        _pg_schema_ready = True


# --- 멱등성(중복 처리 방지) -------------------------------------------------

def try_mark_processed(provider: str, order_id: str) -> bool:
    """order_id를 provider 기준으로 '처리 완료'로 표시한다.

    새로 표시했으면 True(=처음 보는 주문), 이미 있었으면 False(=중복)를
    반환한다. 호출부는 order_id가 빈 값일 때는 아예 호출하지 않아야 한다
    (기존 app.py 로직과 동일하게, ID가 없는 경우는 멱등성 체크 자체를
    스킵하는 게 맞기 때문).
    """
    if _use_db():
        conn = _get_conn()
        try:
            _ensure_schema(conn)
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO processed_orders (provider, order_id) VALUES (%s, %s) "
                    "ON CONFLICT DO NOTHING",
                    (provider, order_id),
                )
                return cur.rowcount == 1
        finally:
            conn.close()

    with _MEM_PROCESSED_LOCK:
        key = (provider, order_id)
        if key in _MEM_PROCESSED:
            return False
        _MEM_PROCESSED.add(key)
        if len(_MEM_PROCESSED) > _MEM_PROCESSED_MAX:
            _MEM_PROCESSED.clear()
            _MEM_PROCESSED.add(key)
        return True


def is_marked_processed(provider: str, order_id: str) -> bool:
    """order_id가 현재 '처리 완료'로 표시돼 있는지 조회만 한다(부작용 없음).
    주로 테스트에서 상태를 확인하는 용도."""
    if _use_db():
        conn = _get_conn()
        try:
            _ensure_schema(conn)
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM processed_orders WHERE provider = %s AND order_id = %s",
                    (provider, order_id),
                )
                return cur.fetchone() is not None
        finally:
            conn.close()

    with _MEM_PROCESSED_LOCK:
        return (provider, order_id) in _MEM_PROCESSED


def unmark_processed(provider: str, order_id: str) -> None:
    """처리 도중 실패했을 때 '처리 완료' 표시를 되돌려서, 재시도(웹훅 재전송)가
    '이미 처리됨'으로 잘못 무시되지 않게 한다."""
    if _use_db():
        conn = _get_conn()
        try:
            _ensure_schema(conn)
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM processed_orders WHERE provider = %s AND order_id = %s",
                    (provider, order_id),
                )
        finally:
            conn.close()
        return

    with _MEM_PROCESSED_LOCK:
        _MEM_PROCESSED.discard((provider, order_id))


# --- Digistore24 보류 주문(개인정보 토큰화) ---------------------------------

def store_pending_order(token: str, data: dict) -> None:
    if _use_db():
        from psycopg2.extras import Json

        conn = _get_conn()
        try:
            _ensure_schema(conn)
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO pending_orders (token, data, created_at) VALUES (%s, %s, now()) "
                    "ON CONFLICT (token) DO UPDATE SET data = EXCLUDED.data, created_at = EXCLUDED.created_at",
                    (token, Json(data)),
                )
        finally:
            conn.close()
        return

    with _MEM_PENDING_LOCK:
        _MEM_PENDING[token] = {"data": data, "created_at": time.time()}


def get_pending_order(token: str):
    """토큰으로 보류 주문을 조회한다. 없으면 None, 있으면
    {"data": dict, "created_at": float(epoch)}를 반환한다."""
    if not token:
        return None

    if _use_db():
        conn = _get_conn()
        try:
            _ensure_schema(conn)
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT data, EXTRACT(EPOCH FROM created_at) FROM pending_orders WHERE token = %s",
                    (token,),
                )
                row = cur.fetchone()
                if not row:
                    return None
                data = dict(row[0])
                claim = data.pop("_claim", None)
                return {"data": data, "created_at": float(row[1]), "claim": claim}
        finally:
            conn.close()

    with _MEM_PENDING_LOCK:
        entry = _MEM_PENDING.get(token)
        if not entry:
            return None
        data = dict(entry["data"])
        claim = data.pop("_claim", None)
        return {"data": data, "created_at": entry["created_at"], "claim": claim}


# --- 생성 중 서버가 죽은 주문 복구 -------------------------------------------
# 결제 웹훅이 접수되면 보류 주문에 "_claim"(provider/order_id/tier/email/started_at/recoveries)을
# 기록한다. 생성이 성공하면 보류 주문 자체가 삭제되므로, 오래된 _claim이 남아 있다는 것은
# (배포 재시작 등으로) 생성이 끝나지 못했다는 뜻이다. recover_stalled_orders가 이를 찾아 준다.

def claim_pending_order(token: str, claim: dict) -> bool:
    """보류 주문에 접수 기록(_claim)을 남긴다. 주문이 없으면 False."""
    if not token:
        return False
    if _use_db():
        from psycopg2.extras import Json

        conn = _get_conn()
        try:
            _ensure_schema(conn)
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE pending_orders SET data = jsonb_set(data, '{_claim}', %s::jsonb) WHERE token = %s",
                    (Json(claim), token),
                )
                return cur.rowcount == 1
        finally:
            conn.close()
    with _MEM_PENDING_LOCK:
        entry = _MEM_PENDING.get(token)
        if not entry:
            return False
        entry["data"]["_claim"] = dict(claim)
        return True


def list_stalled_claims(stale_seconds: int) -> list:
    """started_at이 stale_seconds보다 오래된 _claim이 남은 보류 주문 목록.
    각 항목: {"token", "data"(_claim 제외), "claim"}."""
    cutoff = time.time() - stale_seconds
    rows = []
    if _use_db():
        conn = _get_conn()
        try:
            _ensure_schema(conn)
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT token, data FROM pending_orders WHERE data ? '_claim' "
                    "AND (data->'_claim'->>'started_at')::float < %s",
                    (cutoff,),
                )
                for token, data in cur.fetchall():
                    data = dict(data)
                    rows.append({"token": token, "claim": data.pop("_claim"), "data": data})
        finally:
            conn.close()
        return rows
    with _MEM_PENDING_LOCK:
        for token, entry in _MEM_PENDING.items():
            claim = entry["data"].get("_claim")
            if claim and float(claim.get("started_at", 0)) < cutoff:
                data = {k: v for k, v in entry["data"].items() if k != "_claim"}
                rows.append({"token": token, "claim": dict(claim), "data": data})
    return rows


def cas_claim(token: str, old_started_at: float, new_claim: dict) -> bool:
    """원자적 compare-and-set: 여전히 old_started_at인 _claim만 new_claim으로 교체한다.
    여러 워커가 동시에 같은 주문을 복구하려 할 때 한 쪽만 True를 받는다."""
    if _use_db():
        from psycopg2.extras import Json

        conn = _get_conn()
        try:
            _ensure_schema(conn)
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE pending_orders SET data = jsonb_set(data, '{_claim}', %s::jsonb) "
                    "WHERE token = %s AND (data->'_claim'->>'started_at')::float = %s",
                    (Json(new_claim), token, float(old_started_at)),
                )
                return cur.rowcount == 1
        finally:
            conn.close()
    with _MEM_PENDING_LOCK:
        entry = _MEM_PENDING.get(token)
        claim = entry["data"].get("_claim") if entry else None
        if not claim or float(claim.get("started_at", 0)) != float(old_started_at):
            return False
        entry["data"]["_claim"] = dict(new_claim)
        return True


def pending_token_exists(token: str) -> bool:
    return get_pending_order(token) is not None


def delete_pending_order(token: str) -> None:
    if not token:
        return
    if _use_db():
        conn = _get_conn()
        try:
            _ensure_schema(conn)
            with conn.cursor() as cur:
                cur.execute("DELETE FROM pending_orders WHERE token = %s", (token,))
        finally:
            conn.close()
        return

    with _MEM_PENDING_LOCK:
        _MEM_PENDING.pop(token, None)


def sweep_expired_pending_orders(ttl_seconds: int) -> None:
    """오래 방치된(장바구니 이탈) 보류 주문을 정리한다."""
    if _use_db():
        conn = _get_conn()
        try:
            _ensure_schema(conn)
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM pending_orders WHERE created_at < now() - (%s || ' seconds')::interval",
                    (ttl_seconds,),
                )
        finally:
            conn.close()
        return

    cutoff = time.time() - ttl_seconds
    with _MEM_PENDING_LOCK:
        expired = [tok for tok, entry in _MEM_PENDING.items() if entry["created_at"] < cutoff]
        for tok in expired:
            _MEM_PENDING.pop(tok, None)


# --- 무료 신청 메타(출처/관심사) 집계 -----------------------------------------
# 이메일·이름 등 개인 식별 정보는 저장하지 않는다. (src, interest, lang, 시각)만.
_MEM_SIGNUP_META = []  # [(created_at_epoch, src, interest, lang)]
_MEM_SIGNUP_META_LOCK = threading.Lock()
_MEM_SIGNUP_META_MAX = 5000


def record_signup_meta(src: str, interest: str, lang: str) -> None:
    if _use_db():
        conn = _get_conn()
        try:
            _ensure_schema(conn)
            with conn.cursor() as cur:
                cur.execute(
                    "CREATE TABLE IF NOT EXISTS signup_meta ("
                    "id BIGSERIAL PRIMARY KEY, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), "
                    "src TEXT NOT NULL, interest TEXT NOT NULL, lang TEXT NOT NULL)"
                )
                cur.execute(
                    "INSERT INTO signup_meta (src, interest, lang) VALUES (%s, %s, %s)",
                    (src, interest, lang),
                )
        finally:
            conn.close()
        return
    with _MEM_SIGNUP_META_LOCK:
        _MEM_SIGNUP_META.append((time.time(), src, interest, lang))
        if len(_MEM_SIGNUP_META) > _MEM_SIGNUP_META_MAX:
            del _MEM_SIGNUP_META[0]


def signup_meta_stats(days: int = 30) -> list:
    """[{src, interest, lang, count}] — 최근 days일, 많은 순."""
    if _use_db():
        conn = _get_conn()
        try:
            _ensure_schema(conn)
            with conn.cursor() as cur:
                cur.execute(
                    "CREATE TABLE IF NOT EXISTS signup_meta ("
                    "id BIGSERIAL PRIMARY KEY, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), "
                    "src TEXT NOT NULL, interest TEXT NOT NULL, lang TEXT NOT NULL)"
                )
                cur.execute(
                    "SELECT src, interest, lang, count(*) FROM signup_meta "
                    "WHERE created_at > now() - make_interval(days => %s) "
                    "GROUP BY src, interest, lang ORDER BY count(*) DESC",
                    (int(days),),
                )
                return [
                    {"src": r[0], "interest": r[1], "lang": r[2], "count": r[3]}
                    for r in cur.fetchall()
                ]
        finally:
            conn.close()
    cutoff = time.time() - days * 86400
    counts = {}
    with _MEM_SIGNUP_META_LOCK:
        for ts, src, interest, lang in _MEM_SIGNUP_META:
            if ts >= cutoff:
                counts[(src, interest, lang)] = counts.get((src, interest, lang), 0) + 1
    return [
        {"src": k[0], "interest": k[1], "lang": k[2], "count": v}
        for k, v in sorted(counts.items(), key=lambda kv: -kv[1])
    ]


# --- 방문 집계(쿠키·IP·UA 저장 없음, 일자/출처/경로별 카운트만) -----------------
_MEM_HITS = {}  # (day_iso, src, path) -> n
_MEM_HITS_LOCK = threading.Lock()


def _ensure_hits_table(conn):
    with conn.cursor() as cur:
        cur.execute(
            "CREATE TABLE IF NOT EXISTS page_hits ("
            "day DATE NOT NULL, src TEXT NOT NULL, path TEXT NOT NULL, "
            "n INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (day, src, path))"
        )


SITES = ("de", "en", "fr", "es")


def _enc(base: str, site: str) -> str:
    """사이트 정보를 기존 PK(path/ev)에 접미사로 담는다(스키마 변경 없음). de는 기존 행과 동일."""
    return base if site in ("", "de", None) else f"{base}|{site}"


def split_site(key: str):
    """'/x|fr' -> ('/x', 'fr'); 접미사 없으면 ('/x', 'de')."""
    base, sep, site = (key or "").rpartition("|")
    if sep and site in SITES:
        return base, site
    return key, "de"


def record_hit(src: str, path: str, site: str = "de") -> None:
    """오늘(UTC) 날짜의 (src, path[, site]) 카운트를 1 올린다."""
    path = _enc(path, site)
    day = time.strftime("%Y-%m-%d", time.gmtime())
    if _use_db():
        conn = _get_conn()
        try:
            _ensure_hits_table(conn)
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO page_hits (day, src, path, n) VALUES (%s, %s, %s, 1) "
                    "ON CONFLICT (day, src, path) DO UPDATE SET n = page_hits.n + 1",
                    (day, src, path),
                )
        finally:
            conn.close()
        return
    with _MEM_HITS_LOCK:
        k = (day, src, path)
        _MEM_HITS[k] = _MEM_HITS.get(k, 0) + 1


def hits_stats(days: int = 14) -> list:
    """[{day, src, path, n}] 최근 days일."""
    if _use_db():
        conn = _get_conn()
        try:
            _ensure_hits_table(conn)
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT day::text, src, path, n FROM page_hits "
                    "WHERE day > (now() at time zone 'utc')::date - %s ORDER BY day DESC",
                    (int(days),),
                )
                return [{"day": r[0], "src": r[1], "path": r[2], "n": r[3]} for r in cur.fetchall()]
        finally:
            conn.close()
    cutoff = time.strftime("%Y-%m-%d", time.gmtime(time.time() - days * 86400))
    with _MEM_HITS_LOCK:
        return [
            {"day": d, "src": s, "path": p, "n": n}
            for (d, s, p), n in sorted(_MEM_HITS.items(), reverse=True)
            if d > cutoff
        ]


_MEM_EVENTS = {}  # (day_iso, src, ev) -> n


def _ensure_events_table(conn):
    with conn.cursor() as cur:
        cur.execute(
            "CREATE TABLE IF NOT EXISTS page_events ("
            "day DATE NOT NULL, src TEXT NOT NULL, ev TEXT NOT NULL, "
            "n INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (day, src, ev))"
        )


def record_event(src: str, ev: str, site: str = "de") -> None:
    """오늘(UTC) 날짜의 (src, ev[, site]) 퍼널 이벤트 카운트를 1 올린다. 개인정보 없음."""
    ev = _enc(ev, site)
    day = time.strftime("%Y-%m-%d", time.gmtime())
    if _use_db():
        conn = _get_conn()
        try:
            _ensure_events_table(conn)
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO page_events (day, src, ev, n) VALUES (%s, %s, %s, 1) "
                    "ON CONFLICT (day, src, ev) DO UPDATE SET n = page_events.n + 1",
                    (day, src, ev),
                )
        finally:
            conn.close()
        return
    with _MEM_HITS_LOCK:
        k = (day, src, ev)
        _MEM_EVENTS[k] = _MEM_EVENTS.get(k, 0) + 1


def events_stats(days: int = 14) -> list:
    """[{day, src, ev, n}] 최근 days일."""
    if _use_db():
        conn = _get_conn()
        try:
            _ensure_events_table(conn)
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT day::text, src, ev, n FROM page_events "
                    "WHERE day > (now() at time zone 'utc')::date - %s ORDER BY day DESC",
                    (int(days),),
                )
                return [{"day": r[0], "src": r[1], "ev": r[2], "n": r[3]} for r in cur.fetchall()]
        finally:
            conn.close()
    cutoff = time.strftime("%Y-%m-%d", time.gmtime(time.time() - days * 86400))
    with _MEM_HITS_LOCK:
        return [
            {"day": d, "src": s, "ev": e, "n": n}
            for (d, s, e), n in sorted(_MEM_EVENTS.items(), reverse=True)
            if d > cutoff
        ]


def signups_daily(days: int = 14) -> list:
    """[{day, src, count}] 무료 신청 일별(출처별)."""
    if _use_db():
        conn = _get_conn()
        try:
            _ensure_schema(conn)
            with conn.cursor() as cur:
                cur.execute(
                    "CREATE TABLE IF NOT EXISTS signup_meta ("
                    "id BIGSERIAL PRIMARY KEY, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), "
                    "src TEXT NOT NULL, interest TEXT NOT NULL, lang TEXT NOT NULL)"
                )
                cur.execute(
                    "SELECT (created_at at time zone 'utc')::date::text, src, count(*), lang FROM signup_meta "
                    "WHERE created_at > now() - make_interval(days => %s) GROUP BY 1, 2, 4 ORDER BY 1 DESC",
                    (int(days),),
                )
                return [{"day": r[0], "src": r[1], "count": r[2], "lang": r[3]} for r in cur.fetchall()]
        finally:
            conn.close()
    cutoff = time.time() - days * 86400
    out = {}
    with _MEM_SIGNUP_META_LOCK:
        for ts, src, _i, _l in _MEM_SIGNUP_META:
            if ts >= cutoff:
                k = (time.strftime("%Y-%m-%d", time.gmtime(ts)), src, _l)
                out[k] = out.get(k, 0) + 1
    return [{"day": k[0], "src": k[1], "count": v, "lang": k[2]} for k, v in sorted(out.items(), reverse=True)]


def orders_daily(days: int = 14) -> list:
    """[{day, provider, count}] 처리 완료 주문(결제 완료 후 리포트 처리된 건) 일별.
    메모리 모드에서는 시각을 저장하지 않으므로 빈 목록."""
    if not _use_db():
        return []
    conn = _get_conn()
    try:
        _ensure_schema(conn)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT (processed_at at time zone 'utc')::date::text, provider, count(*) "
                "FROM processed_orders WHERE processed_at > now() - make_interval(days => %s) "
                "GROUP BY 1, 2 ORDER BY 1 DESC",
                (int(days),),
            )
            return [{"day": r[0], "provider": r[1], "count": r[2]} for r in cur.fetchall()]
    finally:
        conn.close()


def reset_for_tests():
    """테스트 전용 — 메모리 상태를 초기화한다.

    테스트는 DATABASE_URL을 설정하지 않은 메모리 모드로 돌아가는 것을
    전제로 한다 (실제 Postgres는 테스트 환경에서 사용할 수 없으므로).
    """
    with _MEM_PROCESSED_LOCK:
        _MEM_PROCESSED.clear()
    with _MEM_PENDING_LOCK:
        _MEM_PENDING.clear()
    with _MEM_SIGNUP_META_LOCK:
        _MEM_SIGNUP_META.clear()
    with _MEM_HITS_LOCK:
        _MEM_HITS.clear()
