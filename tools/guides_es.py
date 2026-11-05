UI = dict(
 back="← Volver a Palja", all="Todas las guías",
 cta_h="Tu perfil de los Cinco Elementos, gratis",
 cta_p="A partir de tu fecha de nacimiento (y de la hora, si la conoces) creamos tu perfil personal según el Saju coreano.",
 btn="Crear mi perfil gratis",
 note="El Saju es un arte de interpretación tradicional y se ofrece aquí para el entretenimiento y la reflexión personal. No contiene predicciones ni sustituye el asesoramiento profesional.",
 index_title="Guías: el Saju y el horóscopo chino", index_h1="Guías",
 index_desc="Guías sobre el Saju, el horóscopo chino y los Cinco Elementos, explicadas con claridad desde la perspectiva coreana.",
 index_intro="El Saju y el horóscopo chino, explicados con claridad. Todo para el entretenimiento y la reflexión personal, sin predicciones.")
SLUGS = dict(horoscope="horoscopo-chino-2027", newyear="ano-nuevo-chino-2027", calc="calcular-signo-chino", elements="cinco-elementos-saju",
 gapja="ciclo-de-60-anos-gapja-hwangap", sheep="ano-de-la-cabra-de-fuego-2027", ddi="zodiaco-coreano-ddi", bazi="saju-y-bazi-diferencias",
 ilju="pilar-del-dia-ilju-saju", pillars="cuatro-pilares-saju", yinyang="yin-y-yang-saju")
ANIM = [("Rata","1972, 1984, 1996, 2008, 2020"),("Buey","1973, 1985, 1997, 2009, 2021"),("Tigre","1974, 1986, 1998, 2010, 2022"),("Conejo","1975, 1987, 1999, 2011, 2023"),
 ("Dragón","1976, 1988, 2000, 2012, 2024"),("Serpiente","1977, 1989, 2001, 2013, 2025"),("Caballo","1978, 1990, 2002, 2014, 2026"),("Cabra","1979, 1991, 2003, 2015, 2027"),
 ("Mono","1968, 1980, 1992, 2004, 2016"),("Gallo","1969, 1981, 1993, 2005, 2017"),("Perro","1970, 1982, 1994, 2006, 2018"),("Cerdo","1971, 1983, 1995, 2007, 2019")]
GEN = "Sin una relación especial con la Cabra. El tema del año (Fuego y Tierra) actúa de forma más bien general."
REL = {"Rata":GEN,"Buey":"El Buey y la Cabra se encuentran frente a frente en el zodiaco (丑未, «oposición»). Tradicionalmente se lee como un tema de tensión y cambio.","Tigre":GEN,
 "Conejo":"Conejo, Cabra y Cerdo forman la «tríada de Madera» (亥卯未), una constelación que une.","Dragón":GEN,"Serpiente":GEN,
 "Caballo":"El Caballo y la Cabra se consideran una «pareja» (午未, armonía), una de las combinaciones clásicas más favorables.",
 "Cabra":"Vuelve tu propio signo. Tradicionalmente se lee como un año en el que uno se mira más a sí mismo.","Mono":GEN,"Gallo":GEN,
 "Perro":"El Perro y la Cabra están en «fricción» (戌未, castigo/Xing). Tradicionalmente se lee como un tema de fricción y aclaración.",
 "Cerdo":"Cerdo, Conejo y Cabra forman la «tríada de Madera» (亥卯未), una constelación que une."}
T1 = "".join(f"<tr><td>{a}</td><td>{y}</td></tr>" for a,y in ANIM)
T2 = "".join(f"<tr><td>{a}</td><td>{REL[a]}</td></tr>" for a,_ in ANIM)
ARTICLES = {
"horoscope": dict(
 title="Horóscopo chino 2027: el año de la Cabra de Fuego", h1="Horóscopo chino 2027: el año de la Cabra de Fuego",
 desc="2027 es el año 丁未, la Cabra de Fuego, en los calendarios chino y coreano. Qué significa, cuándo empieza el año y cómo se relacionan los doce animales.",
 index_title="Horóscopo chino 2027: el año de la Cabra de Fuego",
 index_desc="2027 es el año 丁未 en los calendarios chino y coreano, la Cabra de Fuego (también llamada Oveja).",
 lead="2027 es el año 丁未 (Jeongmi) en los calendarios chino y coreano: la Cabra de Fuego (el animal también se llama Oveja o Carnero). Aquí descubres cuándo empieza realmente este año, qué significan los signos y cómo se relacionan tradicionalmente los doce animales con la Cabra.",
 body=f'''<h2>¿Qué significa 丁未?</h2>
<p>En el calendario de Asia Oriental cada año tiene dos signos: un <strong>Tronco Celeste</strong> (diez posibilidades) y una <strong>Rama Terrestre</strong> (doce posibilidades, los animales). En 2027 la combinación es 丁未.</p>
<ul>
<li><strong>丁 (Ding)</strong> representa el Fuego Yin: la llama tranquila, el calor, la expresión, la luz a pequeña escala.</li>
<li><strong>未 (Wei)</strong> es la Cabra. Su elemento asociado es la Tierra y representa el final del verano.</li>
</ul>
<p>De ahí surge la imagen de la «Cabra de Fuego»: Fuego y Tierra, es decir, calor sobre suelo firme. Cuánto se quiera leer en una imagen así es cuestión de interpretación.</p>

<h2>¿Cuándo empieza realmente el año?</h2>
<p>El año Saju no empieza el 1 de enero ni con el Año Nuevo lunar, sino en <strong>Lichun</strong> (立春, «inicio de la primavera»), alrededor del 4 de febrero. Quien nace en enero de 2027 pertenece al animal del año anterior, es decir, al Caballo (2026). Quien nace en diciembre tiene el animal del año en curso. La hora exacta de Lichun cambia de un año a otro, por lo que quienes cumplen años a principios de febrero deberían calcularlo con precisión.</p>

<h2>¿Qué animal eres?</h2>
<p>Los animales se repiten cada doce años. La siguiente tabla muestra los últimos cinco años de nacimiento de cada animal (para cumpleaños posteriores a Lichun):</p>
<table class="t"><tr><th>Animal</th><th>Años de nacimiento</th></tr>{T1}</table>

<h2>¿Cómo se relacionan los animales con la Cabra?</h2>
<p>La tradición describe relaciones entre los animales: armonías, oposiciones, fricciones y tríadas. Esta es una lectura tradicional para 2027. Es un punto de partida para reflexionar, no un pronóstico:</p>
<table class="t"><tr><th>Tu animal</th><th>Relación con el año de la Cabra</th></tr>{T2}</table>

<h2>Por qué el animal es solo una parte</h2>
<p>El animal de tu año de nacimiento es solo uno de ocho signos (de ahí el nombre coreano <em>Palja</em>, 팔자, «ocho signos»). El Saju tiene cuatro pilares: año, mes, día y hora, cada uno con un Tronco Celeste y una Rama Terrestre. El pilar del día se considera tu «yo». Quien solo conoce el animal conoce solo una parte del cuadro.</p>''',
 cta_extra="Si quieres profundizar, después puedes ver el Informe anual 2027 (9,90 €): una guía de reflexión personal a lo largo de los 12 meses del año de la Cabra de Fuego."),
"newyear": dict(
 title="Año Nuevo chino 2027: fecha, animal y costumbres", h1="Año Nuevo chino 2027",
 desc="El Año Nuevo chino 2027 cae el 6 de febrero. Qué animal comienza, cómo se relaciona el Seollal coreano y por qué en el Saju sigue contando Lichun.",
 index_title="Año Nuevo chino 2027: fecha, animal y costumbres",
 index_desc="El Año Nuevo chino 2027 cae el 6 de febrero. Cómo encaja con el Seollal coreano y el año Saju (Lichun).",
 lead="El Año Nuevo chino 2027 cae el 6 de febrero y da comienzo al año de la Cabra. Aquí verás cómo encaja con el Seollal coreano y con el año Saju (Lichun).",
 body='''<h2>Fecha y animal</h2>
<p>El Año Nuevo lunar 2027 es el <strong>6 de febrero de 2027</strong>. Comienza el año 丁未, la Cabra de Fuego. La fecha cambia cada año porque depende del calendario lunar y cae entre finales de enero y mediados de febrero.</p>

<h2>¿Y el Seollal coreano?</h2>
<p>En Corea la fiesta se llama <em>Seollal</em> (설날). También sigue el calendario lunar y normalmente cae el mismo día que el Año Nuevo chino. Es costumbre visitar a la familia, hacer la reverencia a los mayores <em>Sebae</em> (세배) y tomar la sopa <em>Tteokguk</em> (떡국).</p>

<h2>Por qué el Saju cuenta de otra manera</h2>
<p>El Saju no cuenta el año desde el Año Nuevo, sino desde Lichun (alrededor del 4 de febrero). En 2027 Lichun cae, por tanto, dos días antes del Año Nuevo lunar. Quien nace entre esas fechas puede tener un animal distinto en los horóscopos cotidianos que en el Saju. Más información: <a href="{L:calc}">Cómo calcular tu signo del zodiaco chino</a>.</p>

<h2>Sigue leyendo</h2>
<p>La simbología del año se explica en <a href="{L:sheep}">El año de la Cabra de Fuego 2027</a>, y encontrarás un resumen de todos los animales en el <a href="{L:horoscope}">horóscopo chino 2027</a>.</p>'''),
"calc": dict(
 title="Cómo calcular tu signo del zodiaco chino: por qué cuenta Lichun", h1="Cómo calcular tu signo del zodiaco chino",
 desc="Cómo encontrar tu signo del zodiaco chino: el ciclo de doce años, una tabla de años de nacimiento y por qué quienes cumplen años en enero o principios de febrero deben mirarlo con atención.",
 index_title="Cómo calcular tu signo del zodiaco chino",
 index_desc="El ciclo de doce años, una tabla de años de nacimiento y por qué importa Lichun en los nacimientos de enero y principios de febrero.",
 lead="El animal de tu año de nacimiento no depende del 1 de enero. En el Saju cuenta Lichun, el inicio de la primavera alrededor del 4 de febrero. Aquí aprendes el cálculo sencillo y las excepciones.",
 body='''<h2>El cálculo sencillo</h2>
<p>Los doce animales se repiten en un orden fijo: Rata, Buey, Tigre, Conejo, Dragón, Serpiente, Caballo, Cabra, Mono, Gallo, Perro, Cerdo. Si divides el año menos 4 entre 12, el resto indica tu animal (0 = Rata, 1 = Buey, … 11 = Cerdo). Ejemplo: 1990 − 4 = 1986, y 1986 entre 12 da resto 6, es decir, Caballo.</p>

<h2>La excepción: el año empieza en Lichun</h2>
<p>Esto solo vale si naciste <strong>después de Lichun</strong>. En el Saju el año nuevo empieza en el punto solar Lichun, casi siempre el 3, 4 o 5 de febrero. Quien nació antes calcula con el año anterior. Así, quien nació el 20 de enero de 1990 tiene en el Saju el animal de 1989, la Serpiente.</p>

<h2>¿Y el Año Nuevo lunar?</h2>
<p>El Año Nuevo chino o coreano cae entre finales de enero y mediados de febrero y en la vida cotidiana se usa a menudo como cambio de año. Por eso muchos horóscopos populares calculan con él. El Saju, en cambio, calcula con Lichun. Ambas son convenciones establecidas, por lo que dos fuentes pueden dar dos animales distintos para la misma persona.</p>

<h2>Cumpleaños cerca del límite</h2>
<p>Si naciste entre mediados de enero y mediados de febrero, merece la pena un cálculo al día. El momento exacto de Lichun varía unas horas cada año. Palja calcula con los puntos solares reales.</p>

<h2>¿Y el elemento?</h2>
<p>Al animal le corresponde también un Tronco Celeste y, con él, un elemento. Un resumen de los años de nacimiento actuales está en <a href="{L:horoscope}">Horóscopo chino 2027</a>. Cómo se combina todo esto en una carta natal completa se explica en <a href="{L:pillars}">Los cuatro pilares del Saju</a>.</p>'''),
"elements": dict(
 title="Los cinco elementos del Saju: Madera, Fuego, Tierra, Metal, Agua", h1="Los cinco elementos del Saju explicados con sencillez",
 desc="Los cinco elementos (Wuxing/Ohaeng) del Saju explicados con sencillez: significado, palabras clave, ciclo generador y de control, y cómo aparecen en una carta natal.",
 index_title="Los cinco elementos del Saju: Madera, Fuego, Tierra, Metal, Agua",
 index_desc="Significado, palabras clave y los dos ciclos de los cinco elementos (Ohaeng).",
 lead="Madera, Fuego, Tierra, Metal y Agua son el vocabulario básico del Saju. Aquí lees qué representa tradicionalmente cada elemento, cómo se relacionan y por qué se trata de patrones, no de elementos «buenos» o «malos».",
 body='''<h2>Cinco elementos, cinco imágenes</h2>
<p>En coreano se llaman <em>Ohaeng</em> (오행), en chino <em>Wuxing</em> (五行). «Elemento» es algo engañoso: se trata más bien de cinco fases o tipos de movimiento con los que se describen las cosas.</p>
<table class="t"><tr><th>Elemento</th><th>Signo</th><th>Palabras clave tradicionales</th><th>Estación</th></tr>
<tr><td>Madera</td><td>木</td><td>Crecimiento, comienzo, planificación</td><td>Primavera</td></tr>
<tr><td>Fuego</td><td>火</td><td>Calor, expresión, movimiento</td><td>Verano</td></tr>
<tr><td>Tierra</td><td>土</td><td>Centro, estabilidad, equilibrio</td><td>Final del verano</td></tr>
<tr><td>Metal</td><td>金</td><td>Estructura, claridad, corte</td><td>Otoño</td></tr>
<tr><td>Agua</td><td>水</td><td>Fluir, profundidad, adaptación</td><td>Invierno</td></tr></table>

<h2>El ciclo generador</h2>
<p>En el ciclo «generador» cada elemento nutre al siguiente: la Madera alimenta al Fuego, el Fuego se convierte en Tierra (ceniza), la Tierra guarda el Metal, el Metal «recoge» el Agua (la imagen del rocío sobre el metal frío) y el Agua hace crecer la Madera.</p>

<h2>El ciclo de control</h2>
<p>En el ciclo «controlador» un elemento limita a otro: la Madera atraviesa la Tierra, la Tierra contiene el Agua, el Agua apaga el Fuego, el Fuego funde el Metal, el Metal corta la Madera. Es una imagen de equilibrio, no de ataque.</p>

<h2>Dónde están los elementos en tu carta natal</h2>
<p>Cada uno de los cuatro pilares (año, mes, día, hora) tiene dos signos, y cada signo pertenece a un elemento. De ahí resulta una distribución en hasta ocho signos. En la interpretación se observa qué elementos están muy presentes, cuáles faltan y cómo se relacionan entre sí. El elemento del signo del día (el «señor del día») se considera un punto de referencia especialmente importante.</p>

<h2>Un malentendido frecuente</h2>
<p>Un elemento «ausente» no es una carencia en el sentido de un juicio. Es una descripción con la que se puede reflexionar sobre los puntos de apoyo. Más información en <a href="{L:pillars}">Los cuatro pilares del Saju</a>.</p>'''),
"gapja": dict(
 title="El ciclo de 60 años del Saju: Gapja y el 60.º cumpleaños coreano", h1="El ciclo de 60 años del Saju: Gapja y el 60.º cumpleaños coreano",
 desc="Por qué los calendarios chino y coreano solo tienen 60 combinaciones de años, qué significa Gapja (甲子) y por qué los coreanos celebran el 60.º cumpleaños como Hwangap.",
 index_title="El ciclo de 60 años del Saju: Gapja y Hwangap",
 index_desc="Por qué solo hay 60 combinaciones de años y por qué los coreanos celebran el 60.º cumpleaños como Hwangap.",
 lead="Diez Troncos Celestes y doce animales forman en el calendario de Asia Oriental un ciclo de 60 años. Aquí descubres cómo está construido, por qué 2027 es la Cabra de Fuego y qué es el Hwangap coreano.",
 body='''<h2>¿Cómo surge el ciclo de 60 años?</h2>
<p>Los diez <a href="{L:ilju}">Troncos Celestes</a> y las doce Ramas Terrestres (los animales) se combinan en orden: tronco 1 con rama 1, tronco 2 con rama 2 y así sucesivamente. Tras diez pasos los troncos empiezan de nuevo, tras doce las ramas. Ambas series solo vuelven a coincidir en el comienzo tras <strong>60</strong> pasos. Es el mínimo común múltiplo de 10 y 12.</p>
<p>Por eso solo hay 60 combinaciones y no 120: únicamente existen los pares en los que tronco y rama tienen la misma polaridad (Yang con Yang, Yin con Yin).</p>

<h2>Gapja: el comienzo</h2>
<p>La primera combinación se llama 甲子 (<em>Gapja</em>, 갑자): tronco de Madera Yang y Rata. En coreano «Gapja» también se usa en sentido figurado para un capítulo largo o un lapso de tiempo. El ciclo empezó por última vez en 1984; el próximo año Gapja es 2044.</p>

<h2>¿Dónde está 2027?</h2>
<p>2027 es el año 丁未 (<em>Jeongmi</em>), el 44.º año del ciclo, la Cabra de Fuego. El año anterior, 2026, es 丙午, el Caballo de Fuego. Más información en <a href="{L:horoscope}">Horóscopo chino 2027</a>. Como recordatorio: el año Saju empieza con Lichun, alrededor del 4 de febrero, no el 1 de enero.</p>

<h2>Hwangap: el 60.º cumpleaños en Corea</h2>
<p>Quien cumple 60 años ha recorrido el ciclo una vez y vuelve a estar en el signo de su año de nacimiento. En Corea se celebra tradicionalmente como <strong>Hwangap</strong> (환갑, 回甲) con una gran fiesta familiar. Antes, cuando la esperanza de vida era menor, se consideraba un hito especial. Hoy se celebra más bien el 70.º cumpleaños, pero la palabra se ha mantenido.</p>

<h2>¿Y en el perfil Saju?</h2>
<p>El año de nacimiento está en el pilar del año, uno de los cuatro <a href="{L:pillars}">pilares</a>. El mes, el día y la hora también siguen sus propios ciclos de 60. Tu perfil muestra qué combinación hay en cada pilar.</p>'''),
"sheep": dict(
 title="El año de la Cabra de Fuego 2027: simbología, elemento y relaciones entre animales", h1="El año de la Cabra de Fuego 2027 en el Saju",
 desc="La Cabra de Fuego (丁未) en el Saju: el Fuego Yin se encuentra con la Cabra (Tierra). Simbología, relaciones con Caballo, Buey, Perro, Conejo y Cerdo, y qué tener en cuenta al interpretar.",
 index_title="El año de la Cabra de Fuego 2027: simbología y relaciones entre animales",
 index_desc="El Fuego Yin se encuentra con la Cabra (Tierra): simbología y las cuatro relaciones clásicas.",
 lead="La Cabra de Fuego 丁未 une un fuego tranquilo y cálido con la Cabra, que pertenece a la Tierra y al final del verano. Este artículo explica la simbología, las cuatro relaciones clásicas entre animales y por qué aquí la interpretación es siempre una lectura.",
 body='''<h2>Fuego y Tierra: la imagen del año</h2>
<p>En el Saju los cinco elementos (Madera, Fuego, Tierra, Metal, Agua) tienen cada uno una serie de palabras clave. Para el Fuego son calor, expresión y verano; para la Tierra, centro, estabilidad y final del verano. 丁 es <strong>Fuego Yin</strong>: no una hoguera, sino más bien una vela o una brasa. 未, la Cabra, lleva Tierra en sí. Juntos forman una imagen de calor que se asienta sobre suelo firme.</p>
<p>Importante: es lenguaje simbólico. Invita a reflexionar, por ejemplo con la pregunta de dónde, en tu vida, podrían encontrarse ahora el calor y la estabilidad. No dice lo que va a pasar.</p>

<h2>Cuatro relaciones clásicas con la Cabra</h2>
<h3>Caballo y Cabra: armonía (午未)</h3>
<p>El Caballo y la Cabra forman una de las «Seis Armonías». La tradición la describe como una unión amistosa y de apoyo. El año del Caballo 2026 pasa así directamente a un año de la Cabra en el que ambos signos están «uno al lado del otro».</p>
<h3>Buey y Cabra: oposición (丑未)</h3>
<p>El Buey y la Cabra se encuentran exactamente enfrentados en el zodiaco. Esto se llama <em>Chong</em>, literalmente «choque». Tradicionalmente se lee como movimiento, cambio, a veces tensión. No es una constelación «mala», sino una en movimiento.</p>
<h3>Perro y Cabra: fricción (戌未)</h3>
<p>Perro, Buey y Cabra forman juntos una constelación de «castigo» (<em>Xing</em>). Se trata menos de castigo que de fricción: algo que no encaja de inmediato y necesita aclararse.</p>
<h3>Conejo, Cerdo y Cabra: tríada de Madera (亥卯未)</h3>
<p>Cerdo, Conejo y Cabra pertenecen a una «tríada» que en el Saju se asocia con el elemento Madera: crecimiento y comienzo. Se considera una constelación que une.</p>

<h2>¿Y mi propio signo?</h2>
<p>Si tú mismo eres Cabra (nacidos después de Lichun en 2015, 2003, 1991, 1979, 1967 y antes), vives un «año de regreso». En Corea se habla a menudo del <em>año Ddi</em> (띠해), el año del propio animal, tradicionalmente asociado con la repetición y el examen de uno mismo. Algunos ven en él una oportunidad, otros un año de cautela. Ambas son lecturas, no hechos.</p>

<h2>Cómo puedes usar una interpretación así</h2>
<ul>
<li>Como <strong>lista de preguntas</strong>: ¿qué temas (calor, estabilidad, relaciones, imagen de uno mismo) me ocupan ahora?</li>
<li>Como <strong>motivo de conversación</strong> con amigos o familia, como se hace a menudo en Corea al cambiar de año.</li>
<li>No como base para <strong>grandes decisiones</strong> sobre dinero, salud o trabajo.</li>
</ul>
<p>Para empezar, merece la pena el resumen <a href="{L:horoscope}">Horóscopo chino 2027</a>, donde encontrarás tu animal y los años de nacimiento.</p>'''),
"ddi": dict(
 title="Signo del zodiaco coreano (Ddi): los doce animales en coreano", h1="El signo del zodiaco coreano: el Ddi",
 desc="El signo del zodiaco coreano se llama Ddi (띠). Los doce animales con su nombre coreano, el papel de tu propio año Ddi y la relación con el Saju.",
 index_title="Signo del zodiaco coreano (Ddi): los doce animales en coreano",
 index_desc="Los doce animales con su nombre coreano y el papel de tu propio año Ddi.",
 lead="En Corea no solo se pregunta por el signo astrológico, sino también por el <em>Ddi</em> (띠), el animal del año de nacimiento. Aquí encontrarás los doce animales con su nombre coreano.",
 body='''<h2>Los doce animales en coreano</h2>
<table class="t"><tr><th>Español</th><th>Coreano</th><th>Signo</th></tr>
<tr><td>Rata</td><td>쥐 (jwi)</td><td>子</td></tr>
<tr><td>Buey</td><td>소 (so)</td><td>丑</td></tr>
<tr><td>Tigre</td><td>호랑이 (horangi)</td><td>寅</td></tr>
<tr><td>Conejo</td><td>토끼 (tokki)</td><td>卯</td></tr>
<tr><td>Dragón</td><td>용 (yong)</td><td>辰</td></tr>
<tr><td>Serpiente</td><td>뱀 (baem)</td><td>巳</td></tr>
<tr><td>Caballo</td><td>말 (mal)</td><td>午</td></tr>
<tr><td>Cabra</td><td>양 (yang)</td><td>未</td></tr>
<tr><td>Mono</td><td>원숭이 (wonsungi)</td><td>申</td></tr>
<tr><td>Gallo</td><td>닭 (dak)</td><td>酉</td></tr>
<tr><td>Perro</td><td>개 (gae)</td><td>戌</td></tr>
<tr><td>Cerdo</td><td>돼지 (dwaeji)</td><td>亥</td></tr></table>

<h2>El Ddi en la vida cotidiana</h2>
<p>En Corea la pregunta «¿Cuál es tu Ddi?» es una forma muy habitual de iniciar una conversación. Se dice, por ejemplo, «Soy del Ddi del Tigre» (호랑이띠). Cuando el propio animal vuelve en el año nuevo, se habla del <em>año Ddi</em> (띠해), tradicionalmente asociado con mirar atrás y examinarse a uno mismo.</p>

<h2>Ddi y Saju</h2>
<p>El Ddi es solo la Rama Terrestre del pilar del año, uno de los ocho signos de la carta natal. Cómo se relacionan los animales con el año 2027 se explica en <a href="{L:horoscope}">Horóscopo chino 2027</a>. Y cómo determinar correctamente tu animal se explica en <a href="{L:calc}">este artículo</a>.</p>'''),
"bazi": dict(
 title="¿Saju o Bazi? La diferencia entre la tradición coreana y la china", h1="Saju y Bazi: similitudes y diferencias",
 desc="El Saju (Corea) y el Bazi (China) se basan en los mismos cuatro pilares. Qué es igual, dónde difieren las tradiciones y los términos, y por qué aun así merece la pena conocer la diferencia.",
 index_title="¿Saju o Bazi? Tradición coreana y china comparadas",
 index_desc="Los mismos cuatro pilares, distinto idioma y práctica: qué se comparte y qué difiere.",
 lead="Saju y Bazi suenan distinto, pero se apoyan en las mismas bases: cuatro pilares, ocho signos, cinco elementos. Aquí verás qué es igual y dónde difieren el idioma y la práctica.",
 body='''<h2>Las mismas raíces</h2>
<p><em>Bazi</em> (八字, «ocho signos») es el nombre chino, <em>Saju</em> (四柱, «cuatro pilares») el coreano. Ambos términos describen el mismo principio básico: del año, mes, día y hora de nacimiento resultan cuatro pilares con dos signos cada uno. El <em>Palja</em> (팔자) coreano también significa «ocho signos».</p>

<h2>Lo que es igual</h2>
<ul>
<li>Diez Troncos Celestes y doce Ramas Terrestres</li>
<li>Cinco elementos y Yin/Yang</li>
<li>El ciclo de 60 de los pares tronco-rama</li>
<li>El papel del tronco del día como punto de referencia</li>
</ul>

<h2>Dónde hay diferencias</h2>
<ul>
<li><strong>Idioma y términos:</strong> los mismos signos se pronuncian de otra manera y se explican con otras palabras técnicas (Ohaeng en lugar de Wuxing, Ilgan en lugar de Rì Zhǔ).</li>
<li><strong>Práctica cultural:</strong> en Corea la lectura del Saju es una parte habitual del cambio de año y de la planificación de la vida, y suele hacerse de forma conversada.</li>
<li><strong>Corrección horaria:</strong> la forma de determinar la hora de nacimiento (zona horaria, hora local, límite de medianoche) no se trata igual en todas las escuelas.</li>
<li><strong>Escuelas y ponderación:</strong> en ambos países hay distintas corrientes que acentúan los elementos y los ciclos de forma diferente.</li>
</ul>

<h2>¿Qué versión es la «correcta»?</h2>
<p>Ninguna. Ambas son tradiciones de interpretación con su propia historia, no ciencias naturales. Más importante que el nombre es si un proveedor explica con transparencia cómo calcula y deja claro que se trata de reflexión y no de predicción.</p>

<p>Para una introducción a los elementos básicos, mira <a href="{L:pillars}">Los cuatro pilares del Saju</a> y <a href="{L:elements}">Los cinco elementos del Saju</a>.</p>'''),
"ilju": dict(
 title="El pilar del día en el Saju (Ilju): qué dice tu día de nacimiento", h1="El pilar del día en el Saju (Ilju): qué dice tu día de nacimiento",
 desc="El pilar del día (Ilju, 日柱) se considera en el Saju tu «yo». Qué significan el tronco y la rama del día, cuáles son los diez Troncos Celestes y por qué el día no se puede deducir del año.",
 index_title="El pilar del día en el Saju (Ilju): qué dice tu día de nacimiento",
 index_desc="Por qué el tronco del día representa el «yo» y cuáles son los diez Troncos Celestes.",
 lead="De los cuatro pilares de una carta natal Saju, el pilar del día es el más personal: depende únicamente de tu día de nacimiento. Aquí lees qué significa Ilju, qué representa tradicionalmente el tronco del día y cómo usarlo para tu perfil.",
 body='''<h2>¿Qué es el pilar del día?</h2>
<p>La carta natal Saju consta de cuatro pilares: año, mes, día y hora. Cada pilar tiene dos signos, arriba un <strong>Tronco Celeste</strong> y abajo una <strong>Rama Terrestre</strong>. El pilar del día se llama en coreano <em>Ilju</em> (일주, 日柱). Se calcula a partir del día del calendario, no del año de nacimiento, y se repite en un ritmo fijo de 60 días.</p>

<h2>¿Por qué el tronco del día representa el «yo»?</h2>
<p>El signo superior del pilar del día, el <strong>tronco del día</strong> (일간, 日干), se considera en la enseñanza clásica el punto de referencia de toda la carta natal. Todos los demás signos se leen en relación con él: ¿qué lo nutre, qué lo desafía, qué se le parece? Por eso en el Saju se dice a menudo, de forma abreviada, que el tronco del día es «tú mismo». Es una imagen tradicional, no una medición.</p>

<h2>Los diez Troncos Celestes</h2>
<p>Hay diez troncos: un signo Yang y uno Yin para cada uno de los cinco elementos.</p>
<table class="t"><tr><th>Tronco</th><th>Coreano</th><th>Elemento</th><th>Polaridad</th></tr>
<tr><td>甲</td><td>gap (갑)</td><td>Madera</td><td>Yang</td></tr>
<tr><td>乙</td><td>eul (을)</td><td>Madera</td><td>Yin</td></tr>
<tr><td>丙</td><td>byeong (병)</td><td>Fuego</td><td>Yang</td></tr>
<tr><td>丁</td><td>jeong (정)</td><td>Fuego</td><td>Yin</td></tr>
<tr><td>戊</td><td>mu (무)</td><td>Tierra</td><td>Yang</td></tr>
<tr><td>己</td><td>gi (기)</td><td>Tierra</td><td>Yin</td></tr>
<tr><td>庚</td><td>gyeong (경)</td><td>Metal</td><td>Yang</td></tr>
<tr><td>辛</td><td>sin (신)</td><td>Metal</td><td>Yin</td></tr>
<tr><td>壬</td><td>im (임)</td><td>Agua</td><td>Yang</td></tr>
<tr><td>癸</td><td>gye (계)</td><td>Agua</td><td>Yin</td></tr></table>

<h2>¿Y la rama del día?</h2>
<p>Bajo el tronco está la rama del día, uno de los doce animales. Tradicionalmente se lee como el entorno en el que vive el «yo» y a menudo también se asocia con la pareja y la cercanía. Qué animales existen se explica en <a href="{L:ddi}">Signo del zodiaco coreano (Ddi)</a>.</p>

<h2>¿Por qué no puedes calcular tú mismo tu Ilju con rapidez?</h2>
<p>Los días siguen un ciclo continuo de 60 combinaciones que no se rige por meses ni años. Para ello se necesita una tabla de calendario o un cálculo a partir de un día inicial conocido. Además, un día Saju no empieza a la misma hora en todos los métodos, lo que puede influir en los nacimientos en torno a la medianoche. Si quieres estar seguro, haz calcular tu perfil y comprueba la hora de nacimiento.</p>

<h2>¿Cómo se lee el pilar del día?</h2>
<p>Por sí solo, el tronco del día dice poco. Solo junto con los demás pilares surge un cuadro, por ejemplo qué <a href="{L:elements}">cinco elementos</a> están fuerte o débilmente representados. Más sobre la estructura en <a href="{L:pillars}">Los cuatro pilares del Saju</a>.</p>'''),
"pillars": dict(
 title="Los cuatro pilares del Saju: año, mes, día y hora", h1="Los cuatro pilares del Saju explicados",
 desc="¿Qué son los cuatro pilares (Saju, 사주) y los ocho signos (Palja, 팔자)? Estructura, Troncos Celestes, Ramas Terrestres y qué describen tradicionalmente los pilares del año, mes, día y hora.",
 index_title="Los cuatro pilares del Saju: año, mes, día y hora",
 index_desc="Cuatro pilares, ocho signos: la estructura explicada paso a paso.",
 lead="Saju significa literalmente «cuatro pilares». Cada pilar tiene dos signos, juntos forman ocho signos: Palja. Este artículo explica la estructura paso a paso.",
 body='''<h2>Cuatro pilares, ocho signos</h2>
<p>El <em>Saju</em> coreano (사주, 四柱) significa «cuatro pilares». Son el año, el mes, el día y la hora de nacimiento. Cada pilar se compone de un <strong>Tronco Celeste</strong> (arriba) y una <strong>Rama Terrestre</strong> (abajo). Cuatro pilares por dos signos dan ocho signos, en coreano <em>Palja</em> (팔자).</p>

<h2>Troncos Celestes y Ramas Terrestres</h2>
<ul>
<li><strong>Diez Troncos Celestes:</strong> 甲 乙 丙 丁 戊 己 庚 辛 壬 癸. Dos pertenecen a cada uno de los cinco elementos, una vez Yang y otra Yin.</li>
<li><strong>Doce Ramas Terrestres:</strong> 子 丑 寅 卯 辰 巳 午 未 申 酉 戌 亥. Son los doce animales, de la Rata al Cerdo.</li>
</ul>
<p>Tronco y rama se combinan en un par que sigue un ciclo de 60 combinaciones. 2027, por ejemplo, es 丁未.</p>

<h2>Qué describen tradicionalmente los cuatro pilares</h2>
<table class="t"><tr><th>Pilar</th><th>Asociación tradicional</th></tr>
<tr><td>Año</td><td>Origen, familia, entorno exterior</td></tr>
<tr><td>Mes</td><td>Hogar paterno, profesión, entorno en la vida adulta; se considera especialmente formativo</td></tr>
<tr><td>Día</td><td>El yo; el signo superior es el «señor del día»</td></tr>
<tr><td>Hora</td><td>Vida interior, años tardíos, efecto hacia fuera</td></tr></table>
<p>Es una asignación clásica como marco de reflexión. No es una afirmación sobre cómo transcurre realmente una vida.</p>

<h2>Por qué importa la hora de nacimiento</h2>
<p>Sin hora de nacimiento no se puede determinar el pilar de la hora; entonces se trabaja con tres pilares. Además, el mes Saju no empieza el día uno del mes del calendario, sino en puntos solares (los «términos solares»). Por eso la carta natal puede diferir de la fecha del calendario cotidiano, sobre todo en torno al cambio de mes.</p>

<h2>Sigue leyendo</h2>
<p>Los elementos básicos de los signos los encuentras en <a href="{L:elements}">Los cinco elementos del Saju</a> y <a href="{L:yinyang}">Yin y Yang en el Saju</a>.</p>'''),
"yinyang": dict(
 title="Yin y Yang en el Saju: el significado de la polaridad", h1="Yin y Yang en el Saju",
 desc="Yin y Yang en el Saju explicados con sencillez: cómo cada uno de los cinco elementos aparece en dos formas, qué Troncos Celestes son Yin y Yang y cómo usarlo como modelo de reflexión.",
 index_title="Yin y Yang en el Saju: el significado de la polaridad",
 index_desc="Cómo cada uno de los cinco elementos aparece en una forma Yang y una forma Yin.",
 lead="Yin y Yang no son un esquema de bien y mal, sino dos formas de manifestarse de lo mismo. En el Saju cada uno de los cinco elementos recibe una forma Yang y una forma Yin.",
 body='''<h2>Dos formas por elemento</h2>
<p>Los diez Troncos Celestes surgen porque cada uno de los cinco elementos aparece dos veces: una como Yang (hacia fuera, abierto, fuerte), otra como Yin (hacia dentro, fino, condensado).</p>
<table class="t"><tr><th>Elemento</th><th>Yang</th><th>Yin</th></tr>
<tr><td>Madera</td><td>甲 (árbol grande)</td><td>乙 (hierba, flor)</td></tr>
<tr><td>Fuego</td><td>丙 (sol)</td><td>丁 (llama de vela)</td></tr>
<tr><td>Tierra</td><td>戊 (montaña)</td><td>己 (campo)</td></tr>
<tr><td>Metal</td><td>庚 (hacha, espada)</td><td>辛 (joya, aguja)</td></tr>
<tr><td>Agua</td><td>壬 (mar, río)</td><td>癸 (lluvia, rocío)</td></tr></table>
<p>Las imágenes entre paréntesis son las reglas mnemotécnicas habituales de la tradición. Ayudan a recordar, no son una descripción fija del carácter.</p>

<h2>Yin y Yang en los años</h2>
<p>Los años también son Yin o Yang. Los años que terminan en cifra par llevan troncos Yang (2026: 丙, Fuego Yang). Los años que terminan en cifra impar son Yin (2027: 丁, Fuego Yin). Por eso 2026 se describe a menudo como «fuego abierto» y 2027 como «fuego más tranquilo». Véase <a href="{L:sheep}">El año de la Cabra de Fuego 2027</a>.</p>

<h2>Cómo se puede usar</h2>
<p>Como pregunta: ¿dónde, en mi vida, puedo ir ahora hacia fuera y dónde más bien hacia dentro? No es más que un modelo de reflexión y no sustituye el asesoramiento.</p>'''),
}
