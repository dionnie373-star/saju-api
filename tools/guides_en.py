UI = dict(
 back="← Back to Palja", all="All guides",
 cta_h="Your Five Elements profile, free",
 cta_p="From your date of birth (and your birth time, if you know it) we create your personal profile based on Korean Saju.",
 btn="Create my free profile",
 note="Saju is a traditional system of interpretation and is offered here for entertainment and self-reflection. It makes no predictions and is no substitute for professional advice.",
 index_title="Guides: Saju and the Chinese zodiac", index_h1="Guides",
 index_desc="Guides to Saju, the Chinese zodiac and the Five Elements, explained clearly from a Korean point of view.",
 index_intro="Saju and the Chinese zodiac, explained clearly. All for entertainment and self-reflection, with no predictions.")
SLUGS = dict(horoscope="chinese-zodiac-2027", newyear="chinese-new-year-2027", calc="calculate-chinese-zodiac", elements="five-elements-saju",
 gapja="sixty-year-cycle-gapja-hwangap", sheep="year-of-the-fire-sheep-2027", ddi="korean-zodiac-ddi", bazi="saju-vs-bazi",
 ilju="day-pillar-ilju-saju", pillars="four-pillars-saju", yinyang="yin-and-yang-saju")
ANIM = [("Rat","1972, 1984, 1996, 2008, 2020"),("Ox","1973, 1985, 1997, 2009, 2021"),("Tiger","1974, 1986, 1998, 2010, 2022"),("Rabbit","1975, 1987, 1999, 2011, 2023"),
 ("Dragon","1976, 1988, 2000, 2012, 2024"),("Snake","1977, 1989, 2001, 2013, 2025"),("Horse","1978, 1990, 2002, 2014, 2026"),("Sheep","1979, 1991, 2003, 2015, 2027"),
 ("Monkey","1968, 1980, 1992, 2004, 2016"),("Rooster","1969, 1981, 1993, 2005, 2017"),("Dog","1970, 1982, 1994, 2006, 2018"),("Pig","1971, 1983, 1995, 2007, 2019")]
GEN = "No special relationship with the Sheep. The year's theme (Fire and Earth) works in a more general way."
REL = {"Rat":GEN,"Ox":"Ox and Sheep face each other across the zodiac (丑未, “opposition”). Traditionally this is read as a theme of tension and change.","Tiger":GEN,
 "Rabbit":"Rabbit, Sheep and Pig form the “Wood trine” (亥卯未), a connecting constellation.","Dragon":GEN,"Snake":GEN,
 "Horse":"Horse and Sheep count as a “pair” (午未, harmony), one of the classic friendly combinations.",
 "Sheep":"Your own sign returns. Traditionally this is read as a year in which you look more closely at yourself.","Monkey":GEN,"Rooster":GEN,
 "Dog":"Dog and Sheep are in a “friction” (戌未, punishment/Xing). Traditionally this is read as a theme of friction and clarification.",
 "Pig":"Pig, Rabbit and Sheep form the “Wood trine” (亥卯未), a connecting constellation."}
T1 = "".join(f"<tr><td>{a}</td><td>{y}</td></tr>" for a,y in ANIM)
T2 = "".join(f"<tr><td>{a}</td><td>{REL[a]}</td></tr>" for a,_ in ANIM)
ARTICLES = {
"horoscope": dict(
 title="Chinese Zodiac 2027: The Year of the Fire Sheep", h1="Chinese zodiac 2027: the year of the Fire Sheep",
 desc="2027 is the year 丁未, the Fire Sheep, in the Chinese and Korean calendars. What that means, when the year begins and how the twelve animals relate to it.",
 index_title="Chinese zodiac 2027: the year of the Fire Sheep",
 index_desc="2027 is the year 丁未 in the Chinese and Korean calendars, the Fire Sheep (also called Goat or Ram).",
 lead="2027 is the year 丁未 (Jeongmi) in the Chinese and Korean calendars: the Fire Sheep (in English the animal is also called Goat or Ram). Here you can find out when this year really begins, what the signs mean and how the twelve animals traditionally relate to the Sheep.",
 body=f'''<h2>What does 丁未 mean?</h2>
<p>In the East Asian calendar every year has two characters: a <strong>Heavenly Stem</strong> (ten possibilities) and an <strong>Earthly Branch</strong> (twelve possibilities, the animals). For 2027 the combination is 丁未.</p>
<ul>
<li><strong>丁 (Ding)</strong> stands for Yin Fire: the quiet flame, warmth, expression, light on a small scale.</li>
<li><strong>未 (Wei)</strong> is the Sheep. Its associated element is Earth, and it stands for late summer.</li>
</ul>
<p>This gives the image of the “Fire Sheep”: Fire and Earth, warmth on solid ground. How much to read into such an image is a matter of interpretation.</p>

<h2>When does the year really begin?</h2>
<p>The Saju year begins neither on 1 January nor at Lunar New Year, but at <strong>Lichun</strong> (立春, “start of spring”), around 4 February. Someone born in January 2027 belongs to the animal of the previous year, which is the Horse (2026). Someone born in December has the animal of the current year. The exact time of Lichun changes from year to year, so people with a birthday in early February should calculate carefully.</p>

<h2>Which animal are you?</h2>
<p>The animals repeat every twelve years. The overview below shows the last five birth years for each animal (for birthdays after Lichun):</p>
<table class="t"><tr><th>Animal</th><th>Birth years</th></tr>{T1}</table>

<h2>How do the animals relate to the Sheep?</h2>
<p>The tradition describes relationships between the animals: harmonies, oppositions, frictions and trines. Here is a traditional way of reading 2027. It is food for thought, not a forecast:</p>
<table class="t"><tr><th>Your animal</th><th>Relationship to the Sheep year</th></tr>{T2}</table>

<h2>Why your animal is only one part</h2>
<p>The animal of your birth year is only one of eight characters (hence the Korean name <em>Palja</em>, 팔자, “eight characters”). Saju has four pillars: year, month, day and hour, each with one Heavenly Stem and one Earthly Branch. The day pillar is regarded as your “self”. Anyone who knows only the animal knows only part of the picture.</p>''',
 cta_extra="If you want to go deeper, you can afterwards look at the Annual Report 2027 ($10): a personal reflection guide through all 12 months of the Fire Sheep year."),
"newyear": dict(
 title="Chinese New Year 2027: Date, Animal and Customs", h1="Chinese New Year 2027",
 desc="Chinese New Year 2027 falls on 6 February. Which animal begins, how Korean Seollal relates to it and why Lichun still counts in Saju.",
 index_title="Chinese New Year 2027: date, animal and customs",
 index_desc="Chinese New Year 2027 falls on 6 February. How it fits with Korean Seollal and the Saju year (Lichun).",
 lead="Chinese New Year 2027 falls on 6 February and begins the year of the Sheep. Here is how it fits with Korean Seollal and the Saju year (Lichun).",
 body='''<h2>Date and animal</h2>
<p>Lunar New Year 2027 is on <strong>6 February 2027</strong>. It begins the year 丁未, the Fire Sheep. The date changes every year because it follows the lunar calendar and falls between the end of January and mid-February.</p>

<h2>And Korean Seollal?</h2>
<p>In Korea the festival is called <em>Seollal</em> (설날). It also follows the lunar calendar and usually falls on the same day as Chinese New Year. Family visits, the ancestral bow <em>Sebae</em> (세배) and the soup <em>Tteokguk</em> (떡국) are customary.</p>

<h2>Why Saju counts differently</h2>
<p>Saju does not count the year from New Year but from Lichun (around 4 February). In 2027 Lichun therefore falls two days before Lunar New Year. Someone born between these days can have a different animal in everyday horoscopes than in Saju. More on this: <a href="{L:calc}">How to calculate your Chinese zodiac sign</a>.</p>

<h2>Keep reading</h2>
<p>The symbolism of the year is explained in <a href="{L:sheep}">Year of the Fire Sheep 2027</a>, and you will find an overview of all the animals in the <a href="{L:horoscope}">Chinese zodiac 2027</a>.</p>'''),
"calc": dict(
 title="How to Calculate Your Chinese Zodiac Sign: Why Lichun Counts", h1="How to calculate your Chinese zodiac sign",
 desc="How to find your Chinese zodiac sign: the twelve-year cycle, a table of birth years and why people with a birthday in January or early February should look closely.",
 index_title="How to calculate your Chinese zodiac sign",
 index_desc="The twelve-year cycle, a table of birth years and why Lichun matters for January and early February birthdays.",
 lead="The animal of your birth year does not depend on 1 January. In Saju what counts is Lichun, the start of spring around 4 February. Here you learn the simple calculation and the exceptions.",
 body='''<h2>The simple calculation</h2>
<p>The twelve animals repeat in a fixed order: Rat, Ox, Tiger, Rabbit, Dragon, Snake, Horse, Sheep, Monkey, Rooster, Dog, Pig. If you divide the year minus 4 by 12, the remainder shows your animal (0 = Rat, 1 = Ox, … 11 = Pig). Example: 1990 − 4 = 1986, and 1986 divided by 12 leaves remainder 6, so Horse.</p>

<h2>The exception: the year begins at Lichun</h2>
<p>This only applies if you were born <strong>after Lichun</strong>. In Saju the new year begins at the solar point Lichun, usually on 3, 4 or 5 February. Anyone born before it calculates with the previous year. So someone born on 20 January 1990 has the animal of 1989 in Saju, the Snake.</p>

<h2>And Lunar New Year?</h2>
<p>Chinese or Korean New Year falls between the end of January and mid-February and is often used in everyday life as the turn of the year. Many popular horoscopes therefore use it. Saju, by contrast, counts from Lichun. Both are established conventions, which is why two sources can name two different animals for the same person.</p>

<h2>Birthdays near the boundary</h2>
<p>If you were born between mid-January and mid-February, a day-exact calculation is worthwhile. The exact moment of Lichun shifts by a few hours every year. Palja calculates with the actual solar points.</p>

<h2>And the element?</h2>
<p>A Heavenly Stem, and with it an element, also belongs to the animal. An overview of the current birth years is in <a href="{L:horoscope}">Chinese zodiac 2027</a>. How this comes together in a whole birth chart is explained in <a href="{L:pillars}">The four pillars in Saju</a>.</p>'''),
"elements": dict(
 title="The Five Elements in Saju: Wood, Fire, Earth, Metal, Water", h1="The Five Elements in Saju, explained simply",
 desc="The Five Elements (Wuxing/Ohaeng) in Saju explained simply: meaning, keywords, the generating and controlling cycles and how they appear in a birth chart.",
 index_title="The Five Elements in Saju: Wood, Fire, Earth, Metal, Water",
 index_desc="Meaning, keywords and the two cycles of the Five Elements (Ohaeng).",
 lead="Wood, Fire, Earth, Metal and Water are the basic vocabulary of Saju. Here you can read what each element traditionally stands for, how they connect and why it is about patterns, not “good” or “bad” elements.",
 body='''<h2>Five elements, five images</h2>
<p>In Korean they are called <em>Ohaeng</em> (오행), in Chinese <em>Wuxing</em> (五行). “Element” is slightly misleading here: they are better understood as five phases or kinds of movement used to describe things.</p>
<table class="t"><tr><th>Element</th><th>Character</th><th>Traditional keywords</th><th>Season</th></tr>
<tr><td>Wood</td><td>木</td><td>Growth, beginnings, planning</td><td>Spring</td></tr>
<tr><td>Fire</td><td>火</td><td>Warmth, expression, movement</td><td>Summer</td></tr>
<tr><td>Earth</td><td>土</td><td>Center, stability, balance</td><td>Late summer</td></tr>
<tr><td>Metal</td><td>金</td><td>Structure, clarity, cutting</td><td>Autumn</td></tr>
<tr><td>Water</td><td>水</td><td>Flowing, depth, adaptation</td><td>Winter</td></tr></table>

<h2>The generating cycle</h2>
<p>In the “generating” cycle each element nourishes the next: Wood feeds Fire, Fire becomes Earth (ash), Earth bears Metal, Metal “collects” Water (the image of dew on cold metal) and Water lets Wood grow.</p>

<h2>The controlling cycle</h2>
<p>In the “controlling” cycle one element limits another: Wood penetrates Earth, Earth dams Water, Water puts out Fire, Fire melts Metal, Metal cuts Wood. This is meant as an image of balance, not of attack.</p>

<h2>Where the elements sit in your birth chart</h2>
<p>Each of the four pillars (year, month, day, hour) has two characters, and each character belongs to an element. This gives a distribution across up to eight characters. In interpretation you look at which elements are strongly represented, which are missing and how they relate to each other. The element of the day character (the “day master”) is considered a particularly important reference point.</p>

<h2>A common misunderstanding</h2>
<p>A “missing” element is not a deficiency in the sense of a verdict. It is a description you can use to think about emphasis. More on this in <a href="{L:pillars}">The four pillars in Saju</a>.</p>'''),
"gapja": dict(
 title="The 60-Year Cycle in Saju: Gapja and the Korean 60th Birthday", h1="The 60-year cycle in Saju: Gapja and the Korean 60th birthday",
 desc="Why the Chinese and Korean calendars have only 60 year combinations, what Gapja (甲子) means and why Koreans celebrate the 60th birthday as Hwangap.",
 index_title="The 60-year cycle in Saju: Gapja and Hwangap",
 index_desc="Why there are only 60 year combinations and why Koreans celebrate the 60th birthday as Hwangap.",
 lead="Ten Heavenly Stems and twelve animals make a 60-year cycle in the East Asian calendar. Here you learn how it is built, why 2027 is the Fire Sheep and what the Korean Hwangap is about.",
 body='''<h2>How does the 60-year cycle arise?</h2>
<p>The ten <a href="{L:ilju}">Heavenly Stems</a> and the twelve Earthly Branches (the animals) are combined in order: stem 1 with branch 1, stem 2 with branch 2 and so on. After ten steps the stems start again, after twelve the branches. Both series meet at the beginning again only after <strong>60</strong> steps. That is the least common multiple of 10 and 12.</p>
<p>This is why there are only 60 combinations and not 120: only pairs occur in which stem and branch have the same polarity (Yang with Yang, Yin with Yin).</p>

<h2>Gapja: the beginning</h2>
<p>The first combination is called 甲子 (<em>Gapja</em>, 갑자): Yang Wood stem and Rat. In Korean “Gapja” is also used proverbially for a long chapter or span of time. The cycle most recently began in 1984, and the next Gapja year is 2044.</p>

<h2>Where does 2027 stand?</h2>
<p>2027 is the year 丁未 (<em>Jeongmi</em>), the 44th year of the cycle, the Fire Sheep. The previous year, 2026, is 丙午, the Fire Horse. More in <a href="{L:horoscope}">Chinese zodiac 2027</a>. As a reminder: the Saju year begins with Lichun, around 4 February, not on 1 January.</p>

<h2>Hwangap: the 60th birthday in Korea</h2>
<p>Anyone who turns 60 has gone through the cycle once and is back at the sign of their birth year. In Korea this is traditionally celebrated as <strong>Hwangap</strong> (환갑, 回甲) with a big family party. In the past, when life expectancy was lower, it counted as a special milestone. Today the 70th birthday is often celebrated instead, but the word has stayed.</p>

<h2>And in the Saju profile?</h2>
<p>The year of birth stands in the year pillar, one of four <a href="{L:pillars}">pillars</a>. Month, day and hour also run in their own 60-cycles. Your profile shows which combination stands in each pillar.</p>'''),
"sheep": dict(
 title="Year of the Fire Sheep 2027: Symbolism, Element and Animal Relationships", h1="The year of the Fire Sheep 2027 in Saju",
 desc="The Fire Sheep (丁未) in Saju: Yin Fire meets the Sheep (Earth). Symbolism, relationships with Horse, Ox, Dog, Rabbit and Pig, and what to keep in mind when interpreting.",
 index_title="Year of the Fire Sheep 2027: symbolism and animal relationships",
 index_desc="Yin Fire meets the Sheep (Earth): symbolism and the four classic relationships.",
 lead="The Fire Sheep 丁未 combines a quiet, warming fire with the Sheep, which belongs to Earth and late summer. This article explains the symbolism, the four classic animal relationships and why interpretation here is always reading.",
 body='''<h2>Fire and Earth: the image of the year</h2>
<p>In Saju the five elements (Wood, Fire, Earth, Metal, Water) each have a set of keywords. For Fire these are warmth, expression and summer; for Earth center, stability and late summer. 丁 is <strong>Yin Fire</strong>: not a campfire but more a candle or an ember. 未, the Sheep, carries Earth within it. Together they form an image of warmth settling onto solid ground.</p>
<p>Important: this is symbolic language. It invites reflection, for example with the question of where in your life warmth and stability might be coming together right now. It does not say what will happen.</p>

<h2>Four classic relationships to the Sheep</h2>
<h3>Horse and Sheep: harmony (午未)</h3>
<p>Horse and Sheep form one of the “Six Harmonies”. The tradition describes it as a friendly, supportive connection. The Horse year 2026 therefore passes straight into a Sheep year in which the two signs stand “side by side”.</p>
<h3>Ox and Sheep: opposition (丑未)</h3>
<p>Ox and Sheep sit exactly opposite each other on the zodiac. This is called <em>Chong</em>, literally “clash”. Traditionally it is read as movement, change, sometimes tension. It is not a “bad” constellation, but a lively one.</p>
<h3>Dog and Sheep: friction (戌未)</h3>
<p>Dog, Ox and Sheep together form a “punishment” constellation (<em>Xing</em>). It means less punishment than friction: something that does not fall into place at once and needs clarification.</p>
<h3>Rabbit, Pig and Sheep: Wood trine (亥卯未)</h3>
<p>Pig, Rabbit and Sheep belong to a “trine” that Saju connects with the element Wood: growth and beginnings. It is regarded as a connecting constellation.</p>

<h2>And my own sign?</h2>
<p>If you are a Sheep yourself (birth years after Lichun 2015, 2003, 1991, 1979, 1967 and earlier), you experience a “return year”. In Korea people often speak of the <em>Ddi year</em> (띠해), the year of your own animal, traditionally associated with repetition and self-examination. Some see an opportunity in it, others a year for caution. Both are readings, not facts.</p>

<h2>How you can use such an interpretation</h2>
<ul>
<li>As a <strong>list of questions</strong>: Which themes (warmth, stability, relationships, self-image) are on my mind right now?</li>
<li>As a <strong>conversation starter</strong> with friends or family, as is often done in Korea at the turn of the year.</li>
<li>Not as a basis for <strong>big decisions</strong> such as money, health or career.</li>
</ul>
<p>To get started, the overview <a href="{L:horoscope}">Chinese zodiac 2027</a> is worthwhile, where you will find your animal and the birth years.</p>'''),
"ddi": dict(
 title="Korean Zodiac Sign (Ddi): The Twelve Animals in Korean", h1="Korean zodiac sign: the Ddi",
 desc="The Korean zodiac sign is called Ddi (띠). The twelve animals with their Korean names, the role of your own Ddi year and the link to Saju.",
 index_title="Korean zodiac sign (Ddi): the twelve animals in Korean",
 index_desc="The twelve animals with Korean names and the role of your own Ddi year.",
 lead="In Korea people ask not only about your star sign but also about your <em>Ddi</em> (띠), the animal of your birth year. Here you will find the twelve animals with their Korean names.",
 body='''<h2>The twelve animals in Korean</h2>
<table class="t"><tr><th>English</th><th>Korean</th><th>Character</th></tr>
<tr><td>Rat</td><td>쥐 (jwi)</td><td>子</td></tr>
<tr><td>Ox</td><td>소 (so)</td><td>丑</td></tr>
<tr><td>Tiger</td><td>호랑이 (horangi)</td><td>寅</td></tr>
<tr><td>Rabbit</td><td>토끼 (tokki)</td><td>卯</td></tr>
<tr><td>Dragon</td><td>용 (yong)</td><td>辰</td></tr>
<tr><td>Snake</td><td>뱀 (baem)</td><td>巳</td></tr>
<tr><td>Horse</td><td>말 (mal)</td><td>午</td></tr>
<tr><td>Sheep</td><td>양 (yang)</td><td>未</td></tr>
<tr><td>Monkey</td><td>원숭이 (wonsungi)</td><td>申</td></tr>
<tr><td>Rooster</td><td>닭 (dak)</td><td>酉</td></tr>
<tr><td>Dog</td><td>개 (gae)</td><td>戌</td></tr>
<tr><td>Pig</td><td>돼지 (dwaeji)</td><td>亥</td></tr></table>

<h2>The Ddi in everyday life</h2>
<p>In Korea the question “What is your Ddi?” is a popular conversation opener. People say things like “I'm a Tiger Ddi” (호랑이띠). When your own animal returns in the new year, it is called the <em>Ddi year</em> (띠해), traditionally associated with looking back and self-examination.</p>

<h2>Ddi and Saju</h2>
<p>The Ddi is only the Earthly Branch of the year pillar, one of eight characters in the birth chart. How the animals relate to the year 2027 is in <a href="{L:horoscope}">Chinese zodiac 2027</a>. And how to determine your animal correctly is explained in <a href="{L:calc}">this article</a>.</p>'''),
"bazi": dict(
 title="Saju or Bazi? The Difference Between the Korean and Chinese System", h1="Saju and Bazi: similarities and differences",
 desc="Saju (Korea) and Bazi (China) are based on the same four pillars. What is the same, where traditions and terms differ and why it is still worth knowing the difference.",
 index_title="Saju or Bazi? Korean and Chinese tradition compared",
 index_desc="Same four pillars, different language and practice: what is shared and what differs.",
 lead="Saju and Bazi sound different but build on the same foundations: four pillars, eight characters, five elements. Here is what is the same and where language and practice differ.",
 body='''<h2>Same roots</h2>
<p><em>Bazi</em> (八字, “eight characters”) is the Chinese name, <em>Saju</em> (四柱, “four pillars”) the Korean one. Both terms describe the same basic principle: from the year, month, day and hour of birth you get four pillars with two characters each. The Korean <em>Palja</em> (팔자) also means “eight characters”.</p>

<h2>What is the same</h2>
<ul>
<li>Ten Heavenly Stems and twelve Earthly Branches</li>
<li>Five elements and Yin/Yang</li>
<li>The 60-cycle of stem-branch pairs</li>
<li>The role of the day stem as a reference point</li>
</ul>

<h2>Where there are differences</h2>
<ul>
<li><strong>Language and terms:</strong> The same characters are pronounced differently and explained with different technical words (Ohaeng instead of Wuxing, Ilgan instead of Rì Zhǔ).</li>
<li><strong>Cultural practice:</strong> In Korea Saju reading is a common part of the turn of the year and of life planning, and tends to be conversation-oriented.</li>
<li><strong>Time correction:</strong> How the hour of birth is determined (time zone, local time, midnight boundary) is not handled the same way in every school.</li>
<li><strong>Schools and weighting:</strong> In both countries there are different approaches that emphasize elements and cycles differently.</li>
</ul>

<h2>Which version is “right”?</h2>
<p>Neither. Both are traditions of interpretation with their own history, not natural science. More important than the name is whether a provider explains transparently how it calculates and states clearly that this is about reflection, not prediction.</p>

<p>For an introduction to the building blocks, see <a href="{L:pillars}">The four pillars in Saju</a> and <a href="{L:elements}">The Five Elements in Saju</a>.</p>'''),
"ilju": dict(
 title="The Day Pillar in Saju (Ilju): What Your Birthday Says", h1="The day pillar in Saju (Ilju): what your birthday says",
 desc="The day pillar (Ilju, 日柱) is regarded in Saju as your “self”. What the day stem and day branch mean, which ten Heavenly Stems there are and why you cannot derive the day from the year.",
 index_title="The day pillar in Saju (Ilju): what your birthday says",
 index_desc="Why the day stem stands for the “self” and what the ten Heavenly Stems are.",
 lead="Of the four pillars in a Saju birth chart, the day pillar is the most personal: it depends on your birthday alone. Here you can read what Ilju means, what the day stem traditionally stands for and how to use it for your profile.",
 body='''<h2>What is the day pillar?</h2>
<p>The Saju birth chart consists of four pillars: year, month, day and hour. Each pillar has two characters, a <strong>Heavenly Stem</strong> on top and an <strong>Earthly Branch</strong> below. The day pillar is called <em>Ilju</em> (일주, 日柱) in Korean. It is calculated from the calendar day, not from the birth year, and repeats in a fixed 60-day rhythm.</p>

<h2>Why does the day stem stand for the “self”?</h2>
<p>The upper character of the day pillar, the <strong>day stem</strong> (일간, 日干), is regarded in the classical teaching as the reference point of the whole birth chart. All other characters are read in relation to it: what nourishes it, what challenges it, what resembles it? That is why Saju often says, in shorthand, that the day stem is “you yourself”. This is a traditional image, not a measurement.</p>

<h2>The ten Heavenly Stems</h2>
<p>There are ten stems: one Yang and one Yin character for each of the five elements.</p>
<table class="t"><tr><th>Stem</th><th>Korean</th><th>Element</th><th>Polarity</th></tr>
<tr><td>甲</td><td>gap (갑)</td><td>Wood</td><td>Yang</td></tr>
<tr><td>乙</td><td>eul (을)</td><td>Wood</td><td>Yin</td></tr>
<tr><td>丙</td><td>byeong (병)</td><td>Fire</td><td>Yang</td></tr>
<tr><td>丁</td><td>jeong (정)</td><td>Fire</td><td>Yin</td></tr>
<tr><td>戊</td><td>mu (무)</td><td>Earth</td><td>Yang</td></tr>
<tr><td>己</td><td>gi (기)</td><td>Earth</td><td>Yin</td></tr>
<tr><td>庚</td><td>gyeong (경)</td><td>Metal</td><td>Yang</td></tr>
<tr><td>辛</td><td>sin (신)</td><td>Metal</td><td>Yin</td></tr>
<tr><td>壬</td><td>im (임)</td><td>Water</td><td>Yang</td></tr>
<tr><td>癸</td><td>gye (계)</td><td>Water</td><td>Yin</td></tr></table>

<h2>And the day branch?</h2>
<p>Below the stem stands the day branch, one of the twelve animals. It is traditionally read as the surroundings in which the “self” lives, and is often also linked with partnership and closeness. Which animals exist is explained in <a href="{L:ddi}">Korean zodiac sign (Ddi)</a>.</p>

<h2>Why can't you quickly work out your Ilju yourself?</h2>
<p>The days run in a continuous cycle of 60 combinations that does not follow months or years. You need a calendar table or a calculation from a known starting day. In addition, a Saju day does not begin at the same time of day in every method, which can matter for births around midnight. If you want to be sure, have your profile calculated and check the time of birth.</p>

<h2>How do you read the day pillar?</h2>
<p>On its own the day stem says little. Only together with the other pillars does a picture emerge, for example which of the <a href="{L:elements}">five elements</a> are strongly or weakly represented. More about the structure is in <a href="{L:pillars}">The four pillars in Saju</a>.</p>'''),
"pillars": dict(
 title="The Four Pillars in Saju: Year, Month, Day and Hour", h1="The four pillars in Saju explained",
 desc="What are the four pillars (Saju, 사주) and eight characters (Palja, 팔자)? Structure, Heavenly Stems, Earthly Branches and what the year, month, day and hour pillars traditionally describe.",
 index_title="The four pillars in Saju: year, month, day and hour",
 index_desc="Four pillars, eight characters: the structure explained step by step.",
 lead="Saju literally means “four pillars”. Each pillar has two characters, together making eight characters: Palja. This article explains the structure step by step.",
 body='''<h2>Four pillars, eight characters</h2>
<p>The Korean <em>Saju</em> (사주, 四柱) means “four pillars”. These are the year, month, day and hour of birth. Each pillar consists of a <strong>Heavenly Stem</strong> (above) and an <strong>Earthly Branch</strong> (below). Four pillars times two characters make eight characters, in Korean <em>Palja</em> (팔자).</p>

<h2>Heavenly Stems and Earthly Branches</h2>
<ul>
<li><strong>Ten Heavenly Stems:</strong> 甲 乙 丙 丁 戊 己 庚 辛 壬 癸. Two each belong to one of the five elements, once Yang, once Yin.</li>
<li><strong>Twelve Earthly Branches:</strong> 子 丑 寅 卯 辰 巳 午 未 申 酉 戌 亥. These are the twelve animals from Rat to Pig.</li>
</ul>
<p>Stem and branch are combined into a pair that runs in a cycle of 60 combinations. 2027, for example, is 丁未.</p>

<h2>What the four pillars traditionally describe</h2>
<table class="t"><tr><th>Pillar</th><th>Traditional association</th></tr>
<tr><td>Year</td><td>Origin, family, outer environment</td></tr>
<tr><td>Month</td><td>Parental home, career, surroundings in adult life; regarded as especially formative</td></tr>
<tr><td>Day</td><td>The self; the upper character is the “day master”</td></tr>
<tr><td>Hour</td><td>Inner life, later years, outward impression</td></tr></table>
<p>This is a classical assignment as a thinking frame. It is not a statement about how a life actually unfolds.</p>

<h2>Why birth time matters</h2>
<p>Without a birth time the hour pillar cannot be determined; you then work with three pillars. In addition, the Saju month does not begin on the first of the calendar month but at solar points (the “solar terms”). That is why the birth chart can differ from the date in the everyday calendar, especially around the change of month.</p>

<h2>Keep reading</h2>
<p>You will find the building blocks of the characters in <a href="{L:elements}">The Five Elements in Saju</a> and <a href="{L:yinyang}">Yin and Yang in Saju</a>.</p>'''),
"yinyang": dict(
 title="Yin and Yang in Saju: The Meaning of Polarity", h1="Yin and Yang in Saju",
 desc="Yin and Yang in Saju explained simply: how each of the five elements appears in two forms, which Heavenly Stems are Yin and Yang and how to use this as a thinking model.",
 index_title="Yin and Yang in Saju: the meaning of polarity",
 index_desc="How each of the five elements appears in a Yang and a Yin form.",
 lead="Yin and Yang are not a good-versus-bad scheme but two forms in which the same thing appears. In Saju each of the five elements gets a Yang form and a Yin form.",
 body='''<h2>Two forms per element</h2>
<p>The ten Heavenly Stems arise because each of the five elements appears twice: once as Yang (outward, open, strong), once as Yin (inward, fine, condensed).</p>
<table class="t"><tr><th>Element</th><th>Yang</th><th>Yin</th></tr>
<tr><td>Wood</td><td>甲 (large tree)</td><td>乙 (grass, flower)</td></tr>
<tr><td>Fire</td><td>丙 (sun)</td><td>丁 (candle flame)</td></tr>
<tr><td>Earth</td><td>戊 (mountain)</td><td>己 (field)</td></tr>
<tr><td>Metal</td><td>庚 (axe, sword)</td><td>辛 (jewelry, needle)</td></tr>
<tr><td>Water</td><td>壬 (sea, river)</td><td>癸 (rain, dew)</td></tr></table>
<p>The images in brackets are the usual memory aids of the tradition. They help with remembering; they are not a fixed description of character.</p>

<h2>Yin and Yang in the years</h2>
<p>Years are also Yin or Yang. Years that end in an even number carry Yang stems (2026: 丙, Yang Fire). Years ending in an odd digit are Yin (2027: 丁, Yin Fire). That is why 2026 is often described as “open fire” and 2027 as “quieter fire”. See <a href="{L:sheep}">Year of the Fire Sheep 2027</a>.</p>

<h2>How you can use this</h2>
<p>As a question: where in my life may I go outward right now, and where more inward? It is no more than a thinking model, and it does not replace advice.</p>'''),
}
