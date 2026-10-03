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
                return {"data": row[0], "created_at": float(row[1])}
        finally:
            conn.close()

    with _MEM_PENDING_LOCK:
        entry = _MEM_PENDING.get(token)
        return dict(entry) if entry else None


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


def reset_for_tests():
    """테스트 전용 — 메모리 상태를 초기화한다.

    테스트는 DATABASE_URL을 설정하지 않은 메모리 모드로 돌아가는 것을
    전제로 한다 (실제 Postgres는 테스트 환경에서 사용할 수 없으므로).
    """
    with _MEM_PROCESSED_LOCK:
        _MEM_PROCESSED.clear()
    with _MEM_PENDING_LOCK:
        _MEM_PENDING.clear()
