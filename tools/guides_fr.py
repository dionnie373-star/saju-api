UI = dict(
 back="← Retour à Palja", all="Tous les guides",
 cta_h="Ton profil des Cinq Éléments, gratuit",
 cta_p="À partir de ta date de naissance (et de l'heure, si tu la connais), nous créons ton profil personnel selon le Saju coréen.",
 btn="Créer mon profil gratuit",
 note="Le Saju est un art d'interprétation traditionnel, proposé ici pour le divertissement et la réflexion personnelle. Il ne s'agit ni de prédictions ni d'un substitut à un conseil professionnel.",
 index_title="Guides : le Saju et l'horoscope chinois", index_h1="Guides",
 index_desc="Guides sur le Saju, l'horoscope chinois et les Cinq Éléments, expliqués simplement du point de vue coréen.",
 index_intro="Le Saju et l'horoscope chinois, expliqués simplement. Le tout pour le divertissement et la réflexion personnelle, sans prédictions.")
SLUGS = dict(horoscope="horoscope-chinois-2027", newyear="nouvel-an-chinois-2027", calc="calculer-signe-chinois", elements="cinq-elements-saju",
 gapja="cycle-de-60-ans-gapja-hwangap", sheep="annee-de-la-chevre-de-feu-2027", ddi="zodiaque-coreen-ddi", bazi="saju-et-bazi-difference",
 ilju="pilier-du-jour-ilju-saju", pillars="quatre-piliers-saju", yinyang="yin-et-yang-saju")
ANIM = [("Rat","1972, 1984, 1996, 2008, 2020"),("Bœuf","1973, 1985, 1997, 2009, 2021"),("Tigre","1974, 1986, 1998, 2010, 2022"),("Lapin","1975, 1987, 1999, 2011, 2023"),
 ("Dragon","1976, 1988, 2000, 2012, 2024"),("Serpent","1977, 1989, 2001, 2013, 2025"),("Cheval","1978, 1990, 2002, 2014, 2026"),("Chèvre","1979, 1991, 2003, 2015, 2027"),
 ("Singe","1968, 1980, 1992, 2004, 2016"),("Coq","1969, 1981, 1993, 2005, 2017"),("Chien","1970, 1982, 1994, 2006, 2018"),("Cochon","1971, 1983, 1995, 2007, 2019")]
GEN = "Pas de relation particulière avec la Chèvre. Le thème de l'année (Feu et Terre) agit plutôt de façon générale."
REL = {"Rat":GEN,"Bœuf":"Le Bœuf et la Chèvre se font face dans le zodiaque (丑未, « opposition »). On y lit traditionnellement un thème de tension et de changement.","Tigre":GEN,
 "Lapin":"Lapin, Chèvre et Cochon forment la « triade du Bois » (亥卯未), une constellation qui rassemble.","Dragon":GEN,"Serpent":GEN,
 "Cheval":"Le Cheval et la Chèvre forment un « couple » (午未, harmonie), l'une des associations classiques les plus favorables.",
 "Chèvre":"Ton propre signe revient. On y lit traditionnellement une année où l'on se tourne davantage vers soi-même.","Singe":GEN,"Coq":GEN,
 "Chien":"Le Chien et la Chèvre sont en « friction » (戌未, punition/Xing). On y lit traditionnellement un thème de friction et de clarification.",
 "Cochon":"Cochon, Lapin et Chèvre forment la « triade du Bois » (亥卯未), une constellation qui rassemble."}
T1 = "".join(f"<tr><td>{a}</td><td>{y}</td></tr>" for a,y in ANIM)
T2 = "".join(f"<tr><td>{a}</td><td>{REL[a]}</td></tr>" for a,_ in ANIM)
ARTICLES = {
"horoscope": dict(
 title="Horoscope chinois 2027 : l'année de la Chèvre de feu", h1="Horoscope chinois 2027 : l'année de la Chèvre de feu",
 desc="2027 est l'année 丁未, la Chèvre de feu, dans les calendriers chinois et coréen. Ce que cela signifie, quand l'année commence et comment les douze animaux s'y rapportent.",
 index_title="Horoscope chinois 2027 : l'année de la Chèvre de feu",
 index_desc="2027 est l'année 丁未 dans les calendriers chinois et coréen, la Chèvre de feu (aussi appelée Mouton).",
 lead="2027 est l'année 丁未 (Jeongmi) dans les calendriers chinois et coréen : la Chèvre de feu (l'animal est aussi appelé Mouton ou Bélier). Tu découvres ici quand cette année commence vraiment, ce que signifient les signes et comment les douze animaux se rapportent traditionnellement à la Chèvre.",
 body=f'''<h2>Que signifie 丁未 ?</h2>
<p>Dans le calendrier d'Asie de l'Est, chaque année porte deux signes : un <strong>Tronc céleste</strong> (dix possibilités) et une <strong>Branche terrestre</strong> (douze possibilités, les animaux). Pour 2027, la combinaison est 丁未.</p>
<ul>
<li><strong>丁 (Ding)</strong> représente le Feu Yin : la flamme tranquille, la chaleur, l'expression, la lumière à petite échelle.</li>
<li><strong>未 (Wei)</strong> est la Chèvre. Son élément associé est la Terre, et elle correspond à la fin de l'été.</li>
</ul>
<p>De là naît l'image de la « Chèvre de feu » : Feu et Terre, c'est-à-dire de la chaleur sur un sol ferme. La part que l'on veut lire dans une telle image relève de l'interprétation.</p>

<h2>Quand l'année commence-t-elle vraiment ?</h2>
<p>L'année Saju ne commence ni le 1er janvier ni au Nouvel An lunaire, mais à <strong>Lichun</strong> (立春, « début du printemps »), vers le 4 février. Une personne née en janvier 2027 appartient à l'animal de l'année précédente, donc au Cheval (2026). Une personne née en décembre a l'animal de l'année en cours. L'heure exacte de Lichun change d'une année à l'autre ; les personnes dont l'anniversaire tombe début février devraient donc calculer précisément.</p>

<h2>Quel animal es-tu ?</h2>
<p>Les animaux se répètent tous les douze ans. Le tableau ci-dessous montre les cinq dernières années de naissance de chaque animal (pour les anniversaires après Lichun) :</p>
<table class="t"><tr><th>Animal</th><th>Années de naissance</th></tr>{T1}</table>

<h2>Comment les animaux se rapportent-ils à la Chèvre ?</h2>
<p>La tradition décrit des relations entre les animaux : harmonies, oppositions, frictions et triades. Voici une lecture traditionnelle pour 2027. C'est une piste de réflexion, pas un pronostic :</p>
<table class="t"><tr><th>Ton animal</th><th>Relation avec l'année de la Chèvre</th></tr>{T2}</table>

<h2>Pourquoi l'animal n'est qu'une partie</h2>
<p>L'animal de ton année de naissance n'est qu'un des huit signes (d'où le nom coréen <em>Palja</em>, 팔자, « huit signes »). Le Saju comporte quatre piliers : année, mois, jour et heure, chacun avec un Tronc céleste et une Branche terrestre. Le pilier du jour est considéré comme ton « moi ». Qui ne connaît que l'animal ne connaît qu'une partie du tableau.</p>''',
 cta_extra="Si tu veux aller plus loin, tu pourras ensuite découvrir le Rapport annuel 2027 (9,90 €) : un guide de réflexion personnel à travers les 12 mois de l'année de la Chèvre de feu."),
"newyear": dict(
 title="Nouvel An chinois 2027 : date, animal et traditions", h1="Nouvel An chinois 2027",
 desc="Le Nouvel An chinois 2027 tombe le 6 février. Quel animal commence, comment le Seollal coréen s'y rapporte et pourquoi Lichun compte quand même dans le Saju.",
 index_title="Nouvel An chinois 2027 : date, animal et traditions",
 index_desc="Le Nouvel An chinois 2027 tombe le 6 février. Son lien avec le Seollal coréen et l'année Saju (Lichun).",
 lead="Le Nouvel An chinois 2027 tombe le 6 février et ouvre l'année de la Chèvre. Voici comment il s'accorde avec le Seollal coréen et l'année Saju (Lichun).",
 body='''<h2>Date et animal</h2>
<p>Le Nouvel An lunaire 2027 est le <strong>6 février 2027</strong>. Il ouvre l'année 丁未, la Chèvre de feu. La date change chaque année, car elle suit le calendrier lunaire et se situe entre fin janvier et mi-février.</p>

<h2>Et le Seollal coréen ?</h2>
<p>En Corée, la fête s'appelle <em>Seollal</em> (설날). Elle suit elle aussi le calendrier lunaire et tombe en général le même jour que le Nouvel An chinois. On rend visite à la famille, on fait la révérence aux aînés <em>Sebae</em> (세배) et on mange la soupe <em>Tteokguk</em> (떡국).</p>

<h2>Pourquoi le Saju compte autrement</h2>
<p>Le Saju ne compte pas l'année à partir du Nouvel An, mais à partir de Lichun (vers le 4 février). En 2027, Lichun tombe donc deux jours avant le Nouvel An lunaire. Une personne née entre ces deux dates peut avoir un autre animal dans les horoscopes courants que dans le Saju. Plus d'informations : <a href="{L:calc}">Calculer son signe du zodiaque chinois</a>.</p>

<h2>Pour aller plus loin</h2>
<p>La symbolique de l'année est expliquée dans <a href="{L:sheep}">L'année de la Chèvre de feu 2027</a>, et tu trouveras un aperçu de tous les animaux dans l'<a href="{L:horoscope}">horoscope chinois 2027</a>.</p>'''),
"calc": dict(
 title="Calculer son signe du zodiaque chinois : pourquoi Lichun compte", h1="Calculer son signe du zodiaque chinois",
 desc="Comment trouver ton signe du zodiaque chinois : le cycle de douze ans, un tableau des années de naissance et pourquoi les personnes nées en janvier ou début février doivent regarder de près.",
 index_title="Calculer son signe du zodiaque chinois",
 index_desc="Le cycle de douze ans, un tableau des années de naissance et l'importance de Lichun pour les naissances de janvier et début février.",
 lead="L'animal de ton année de naissance ne dépend pas du 1er janvier. Dans le Saju, ce qui compte est Lichun, le début du printemps vers le 4 février. Tu apprends ici le calcul simple et les exceptions.",
 body='''<h2>Le calcul simple</h2>
<p>Les douze animaux se répètent dans un ordre fixe : Rat, Bœuf, Tigre, Lapin, Dragon, Serpent, Cheval, Chèvre, Singe, Coq, Chien, Cochon. Si tu divises l'année moins 4 par 12, le reste indique ton animal (0 = Rat, 1 = Bœuf, … 11 = Cochon). Exemple : 1990 − 4 = 1986, et 1986 divisé par 12 donne un reste de 6, donc Cheval.</p>

<h2>L'exception : l'année commence à Lichun</h2>
<p>Cela ne vaut que si tu es né(e) <strong>après Lichun</strong>. Dans le Saju, la nouvelle année commence au point solaire Lichun, le plus souvent le 3, 4 ou 5 février. Qui est né avant calcule avec l'année précédente. Une personne née le 20 janvier 1990 a donc, dans le Saju, l'animal de 1989 : le Serpent.</p>

<h2>Et le Nouvel An lunaire ?</h2>
<p>Le Nouvel An chinois ou coréen tombe entre fin janvier et mi-février et sert souvent, dans la vie courante, de changement d'année. De nombreux horoscopes populaires calculent donc ainsi. Le Saju, lui, calcule à partir de Lichun. Les deux sont des conventions établies ; c'est pourquoi deux sources peuvent indiquer deux animaux différents pour la même personne.</p>

<h2>Anniversaire près de la limite</h2>
<p>Si tu es né(e) entre la mi-janvier et la mi-février, un calcul au jour près en vaut la peine. Le moment exact de Lichun varie de quelques heures chaque année. Palja calcule avec les véritables points solaires.</p>

<h2>Et l'élément ?</h2>
<p>À l'animal correspond aussi un Tronc céleste, et donc un élément. Un aperçu des années de naissance actuelles se trouve dans <a href="{L:horoscope}">Horoscope chinois 2027</a>. La façon dont tout cela s'assemble dans un thème de naissance complet est expliquée dans <a href="{L:pillars}">Les quatre piliers du Saju</a>.</p>'''),
"elements": dict(
 title="Les cinq éléments du Saju : Bois, Feu, Terre, Métal, Eau", h1="Les cinq éléments du Saju expliqués simplement",
 desc="Les cinq éléments (Wuxing/Ohaeng) du Saju expliqués simplement : signification, mots-clés, cycle d'engendrement et de contrôle, et leur présence dans un thème de naissance.",
 index_title="Les cinq éléments du Saju : Bois, Feu, Terre, Métal, Eau",
 index_desc="Signification, mots-clés et les deux cycles des cinq éléments (Ohaeng).",
 lead="Bois, Feu, Terre, Métal et Eau forment le vocabulaire de base du Saju. Tu lis ici ce que chaque élément représente traditionnellement, comment ils sont liés et pourquoi il s'agit de schémas, pas d'éléments « bons » ou « mauvais ».",
 body='''<h2>Cinq éléments, cinq images</h2>
<p>En coréen, on les appelle <em>Ohaeng</em> (오행), en chinois <em>Wuxing</em> (五行). « Élément » est un peu trompeur : il s'agit plutôt de cinq phases ou types de mouvement avec lesquels on décrit les choses.</p>
<table class="t"><tr><th>Élément</th><th>Signe</th><th>Mots-clés traditionnels</th><th>Saison</th></tr>
<tr><td>Bois</td><td>木</td><td>Croissance, commencement, planification</td><td>Printemps</td></tr>
<tr><td>Feu</td><td>火</td><td>Chaleur, expression, mouvement</td><td>Été</td></tr>
<tr><td>Terre</td><td>土</td><td>Centre, stabilité, équilibre</td><td>Fin d'été</td></tr>
<tr><td>Métal</td><td>金</td><td>Structure, clarté, tranchant</td><td>Automne</td></tr>
<tr><td>Eau</td><td>水</td><td>Écoulement, profondeur, adaptation</td><td>Hiver</td></tr></table>

<h2>Le cycle d'engendrement</h2>
<p>Dans le cycle « engendrant », chaque élément nourrit le suivant : le Bois nourrit le Feu, le Feu devient Terre (cendre), la Terre renferme le Métal, le Métal « recueille » l'Eau (l'image de la rosée sur le métal froid) et l'Eau fait croître le Bois.</p>

<h2>Le cycle de contrôle</h2>
<p>Dans le cycle « contrôlant », un élément en limite un autre : le Bois pénètre la Terre, la Terre endigue l'Eau, l'Eau éteint le Feu, le Feu fait fondre le Métal, le Métal coupe le Bois. C'est une image d'équilibre, pas d'attaque.</p>

<h2>Où se trouvent les éléments dans ton thème de naissance</h2>
<p>Chacun des quatre piliers (année, mois, jour, heure) porte deux signes, et chaque signe appartient à un élément. Il en résulte une répartition sur jusqu'à huit signes. Dans l'interprétation, on regarde quels éléments sont très présents, lesquels manquent et comment ils se situent les uns par rapport aux autres. L'élément du signe du jour (le « maître du jour ») est considéré comme un point de repère particulièrement important.</p>

<h2>Un malentendu fréquent</h2>
<p>Un élément « manquant » n'est pas un défaut au sens d'un jugement. C'est une description qui permet de réfléchir à ses points d'appui. Plus d'informations dans <a href="{L:pillars}">Les quatre piliers du Saju</a>.</p>'''),
"gapja": dict(
 title="Le cycle de 60 ans du Saju : Gapja et le 60e anniversaire coréen", h1="Le cycle de 60 ans du Saju : Gapja et le 60e anniversaire coréen",
 desc="Pourquoi les calendriers chinois et coréen ne comptent que 60 combinaisons d'années, ce que signifie Gapja (甲子) et pourquoi les Coréens fêtent le 60e anniversaire sous le nom de Hwangap.",
 index_title="Le cycle de 60 ans du Saju : Gapja et Hwangap",
 index_desc="Pourquoi il n'y a que 60 combinaisons d'années et pourquoi les Coréens fêtent le 60e anniversaire comme Hwangap.",
 lead="Dix Troncs célestes et douze animaux forment un cycle de 60 ans dans le calendrier d'Asie de l'Est. Tu découvres ici comment il est construit, pourquoi 2027 est la Chèvre de feu et ce qu'est le Hwangap coréen.",
 body='''<h2>Comment naît le cycle de 60 ans ?</h2>
<p>Les dix <a href="{L:ilju}">Troncs célestes</a> et les douze Branches terrestres (les animaux) sont combinés dans l'ordre : tronc 1 avec branche 1, tronc 2 avec branche 2, et ainsi de suite. Après dix pas, les troncs recommencent ; après douze, les branches. Les deux séries ne se retrouvent au début en même temps qu'après <strong>60</strong> pas. C'est le plus petit commun multiple de 10 et de 12.</p>
<p>C'est pourquoi il n'y a que 60 combinaisons et non 120 : seules existent les paires où le tronc et la branche ont la même polarité (Yang avec Yang, Yin avec Yin).</p>

<h2>Gapja : le commencement</h2>
<p>La première combinaison s'appelle 甲子 (<em>Gapja</em>, 갑자) : tronc de Bois Yang et Rat. En coréen, on dit aussi « Gapja » au sens figuré pour un long chapitre ou une longue période. Le cycle a commencé pour la dernière fois en 1984 ; la prochaine année Gapja est 2044.</p>

<h2>Où se situe 2027 ?</h2>
<p>2027 est l'année 丁未 (<em>Jeongmi</em>), la 44e année du cycle, la Chèvre de feu. L'année précédente, 2026, est 丙午, le Cheval de feu. Plus d'informations dans <a href="{L:horoscope}">Horoscope chinois 2027</a>. Pour rappel : l'année Saju commence à Lichun, vers le 4 février, et non le 1er janvier.</p>

<h2>Hwangap : le 60e anniversaire en Corée</h2>
<p>Qui atteint 60 ans a parcouru le cycle une fois et retrouve le signe de son année de naissance. En Corée, on le célèbre traditionnellement sous le nom de <strong>Hwangap</strong> (환갑, 回甲) par une grande fête de famille. Autrefois, quand l'espérance de vie était plus basse, c'était une étape particulière. Aujourd'hui, on fête plutôt le 70e anniversaire, mais le mot est resté.</p>

<h2>Et dans le profil Saju ?</h2>
<p>L'année de naissance figure dans le pilier de l'année, l'un des quatre <a href="{L:pillars}">piliers</a>. Le mois, le jour et l'heure suivent eux aussi leurs propres cycles de 60. Ton profil montre quelle combinaison figure dans chaque pilier.</p>'''),
"sheep": dict(
 title="L'année de la Chèvre de feu 2027 : symbolique, élément et relations entre animaux", h1="L'année de la Chèvre de feu 2027 dans le Saju",
 desc="La Chèvre de feu (丁未) dans le Saju : le Feu Yin rencontre la Chèvre (Terre). Symbolique, relations avec le Cheval, le Bœuf, le Chien, le Lapin et le Cochon, et ce qu'il faut garder à l'esprit.",
 index_title="L'année de la Chèvre de feu 2027 : symbolique et relations entre animaux",
 index_desc="Le Feu Yin rencontre la Chèvre (Terre) : la symbolique et les quatre relations classiques.",
 lead="La Chèvre de feu 丁未 associe un feu calme et réchauffant à la Chèvre, qui appartient à la Terre et à la fin de l'été. Cet article explique la symbolique, les quatre relations classiques entre animaux et pourquoi l'interprétation reste ici toujours une lecture.",
 body='''<h2>Feu et Terre : l'image de l'année</h2>
<p>Dans le Saju, les cinq éléments (Bois, Feu, Terre, Métal, Eau) ont chacun une série de mots-clés. Pour le Feu : chaleur, expression et été ; pour la Terre : centre, stabilité et fin d'été. 丁 est le <strong>Feu Yin</strong> : pas un feu de camp, plutôt une bougie ou une braise. 未, la Chèvre, porte la Terre en elle. Ensemble, cela donne l'image d'une chaleur qui se pose sur un sol ferme.</p>
<p>Important : c'est un langage symbolique. Il invite à réfléchir, par exemple à la question de savoir où, dans ta vie, la chaleur et la stabilité pourraient se rejoindre en ce moment. Il ne dit pas ce qui va arriver.</p>

<h2>Quatre relations classiques avec la Chèvre</h2>
<h3>Cheval et Chèvre : harmonie (午未)</h3>
<p>Le Cheval et la Chèvre forment l'une des « Six Harmonies ». La tradition la décrit comme une relation amicale et favorable. L'année du Cheval 2026 passe donc directement dans une année de la Chèvre où les deux signes se tiennent « côte à côte ».</p>
<h3>Bœuf et Chèvre : opposition (丑未)</h3>
<p>Le Bœuf et la Chèvre se trouvent exactement face à face dans le zodiaque. On l'appelle <em>Chong</em>, littéralement « choc ». On y lit traditionnellement du mouvement, du changement, parfois de la tension. Ce n'est pas une constellation « mauvaise », mais une constellation en mouvement.</p>
<h3>Chien et Chèvre : friction (戌未)</h3>
<p>Chien, Bœuf et Chèvre forment ensemble une constellation de « punition » (<em>Xing</em>). Il s'agit moins de punition que de friction : quelque chose qui ne s'ajuste pas tout de suite et demande à être clarifié.</p>
<h3>Lapin, Cochon et Chèvre : triade du Bois (亥卯未)</h3>
<p>Cochon, Lapin et Chèvre appartiennent à une « triade » que le Saju relie à l'élément Bois : croissance et commencement. Elle est considérée comme une constellation qui rassemble.</p>

<h2>Et mon propre signe ?</h2>
<p>Si tu es toi-même Chèvre (nés après Lichun en 2015, 2003, 1991, 1979, 1967 et avant), tu vis une « année de retour ». En Corée, on parle souvent de l'<em>année Ddi</em> (띠해), l'année de son propre animal, traditionnellement associée à la répétition et à l'examen de soi. Certains y voient une chance, d'autres une année de prudence. Ce sont des lectures, pas des faits.</p>

<h2>Comment utiliser une telle interprétation</h2>
<ul>
<li>Comme une <strong>liste de questions</strong> : quels thèmes (chaleur, stabilité, relations, image de soi) m'occupent en ce moment ?</li>
<li>Comme un <strong>sujet de conversation</strong> avec des amis ou la famille, comme on le fait souvent en Corée au changement d'année.</li>
<li>Pas comme base pour de <strong>grandes décisions</strong> concernant l'argent, la santé ou la carrière.</li>
</ul>
<p>Pour commencer, l'aperçu <a href="{L:horoscope}">Horoscope chinois 2027</a> vaut le détour : tu y trouves ton animal et les années de naissance.</p>'''),
"ddi": dict(
 title="Signe du zodiaque coréen (Ddi) : les douze animaux en coréen", h1="Le signe du zodiaque coréen : le Ddi",
 desc="Le signe du zodiaque coréen s'appelle Ddi (띠). Les douze animaux avec leur nom coréen, le rôle de ta propre année Ddi et le lien avec le Saju.",
 index_title="Signe du zodiaque coréen (Ddi) : les douze animaux en coréen",
 index_desc="Les douze animaux avec leur nom coréen et le rôle de ta propre année Ddi.",
 lead="En Corée, on ne demande pas seulement le signe astrologique, mais aussi le <em>Ddi</em> (띠), l'animal de l'année de naissance. Tu trouveras ici les douze animaux avec leur nom coréen.",
 body='''<h2>Les douze animaux en coréen</h2>
<table class="t"><tr><th>Français</th><th>Coréen</th><th>Signe</th></tr>
<tr><td>Rat</td><td>쥐 (jwi)</td><td>子</td></tr>
<tr><td>Bœuf</td><td>소 (so)</td><td>丑</td></tr>
<tr><td>Tigre</td><td>호랑이 (horangi)</td><td>寅</td></tr>
<tr><td>Lapin</td><td>토끼 (tokki)</td><td>卯</td></tr>
<tr><td>Dragon</td><td>용 (yong)</td><td>辰</td></tr>
<tr><td>Serpent</td><td>뱀 (baem)</td><td>巳</td></tr>
<tr><td>Cheval</td><td>말 (mal)</td><td>午</td></tr>
<tr><td>Chèvre</td><td>양 (yang)</td><td>未</td></tr>
<tr><td>Singe</td><td>원숭이 (wonsungi)</td><td>申</td></tr>
<tr><td>Coq</td><td>닭 (dak)</td><td>酉</td></tr>
<tr><td>Chien</td><td>개 (gae)</td><td>戌</td></tr>
<tr><td>Cochon</td><td>돼지 (dwaeji)</td><td>亥</td></tr></table>

<h2>Le Ddi au quotidien</h2>
<p>En Corée, la question « Quel est ton Ddi ? » est une entrée en matière très courante. On dit par exemple « Je suis du Ddi du Tigre » (호랑이띠). Quand son propre animal revient dans la nouvelle année, on parle de l'<em>année Ddi</em> (띠해), traditionnellement associée au regard en arrière et à l'examen de soi.</p>

<h2>Ddi et Saju</h2>
<p>Le Ddi n'est que la Branche terrestre du pilier de l'année, l'un des huit signes du thème de naissance. La façon dont les animaux se situent par rapport à 2027 est expliquée dans <a href="{L:horoscope}">Horoscope chinois 2027</a>. Et comment déterminer correctement son animal est expliqué dans <a href="{L:calc}">cet article</a>.</p>'''),
"bazi": dict(
 title="Saju ou Bazi ? La différence entre la tradition coréenne et chinoise", h1="Saju et Bazi : points communs et différences",
 desc="Le Saju (Corée) et le Bazi (Chine) reposent sur les mêmes quatre piliers. Ce qui est identique, où les traditions et les termes diffèrent et pourquoi il vaut quand même la peine de connaître la différence.",
 index_title="Saju ou Bazi ? Tradition coréenne et chinoise comparées",
 index_desc="Mêmes quatre piliers, langue et pratique différentes : ce qui est commun et ce qui diffère.",
 lead="Saju et Bazi sonnent différemment, mais reposent sur les mêmes bases : quatre piliers, huit signes, cinq éléments. Voici ce qui est identique et où la langue et la pratique diffèrent.",
 body='''<h2>Les mêmes racines</h2>
<p><em>Bazi</em> (八字, « huit signes ») est le nom chinois, <em>Saju</em> (四柱, « quatre piliers ») le nom coréen. Les deux termes décrivent le même principe de base : à partir de l'année, du mois, du jour et de l'heure de naissance, on obtient quatre piliers de deux signes chacun. Le <em>Palja</em> (팔자) coréen signifie lui aussi « huit signes ».</p>

<h2>Ce qui est identique</h2>
<ul>
<li>Dix Troncs célestes et douze Branches terrestres</li>
<li>Cinq éléments et Yin/Yang</li>
<li>Le cycle de 60 des paires tronc-branche</li>
<li>Le rôle du tronc du jour comme point de repère</li>
</ul>

<h2>Où il y a des différences</h2>
<ul>
<li><strong>Langue et termes :</strong> les mêmes signes se prononcent autrement et s'expliquent avec d'autres termes techniques (Ohaeng au lieu de Wuxing, Ilgan au lieu de Rì Zhǔ).</li>
<li><strong>Pratique culturelle :</strong> en Corée, la lecture du Saju fait couramment partie du changement d'année et de la réflexion sur la vie, et se pratique plutôt sous forme de conversation.</li>
<li><strong>Correction de l'heure :</strong> la manière de déterminer l'heure de naissance (fuseau horaire, heure locale, limite de minuit) n'est pas traitée de la même façon dans toutes les écoles.</li>
<li><strong>Écoles et pondération :</strong> dans les deux pays, il existe différents courants qui accentuent les éléments et les cycles de façon différente.</li>
</ul>

<h2>Quelle version est « la bonne » ?</h2>
<p>Aucune. Les deux sont des traditions d'interprétation avec leur propre histoire, pas des sciences naturelles. Plus important que le nom : un prestataire explique-t-il de façon transparente comment il calcule, et dit-il clairement qu'il s'agit de réflexion et non de prédiction ?</p>

<p>Pour une introduction aux éléments de base, voir <a href="{L:pillars}">Les quatre piliers du Saju</a> et <a href="{L:elements}">Les cinq éléments du Saju</a>.</p>'''),
"ilju": dict(
 title="Le pilier du jour du Saju (Ilju) : ce que dit ton jour de naissance", h1="Le pilier du jour du Saju (Ilju) : ce que dit ton jour de naissance",
 desc="Le pilier du jour (Ilju, 日柱) est considéré dans le Saju comme ton « moi ». Ce que signifient le tronc et la branche du jour, quels sont les dix Troncs célestes et pourquoi on ne peut pas déduire le jour de l'année.",
 index_title="Le pilier du jour du Saju (Ilju) : ce que dit ton jour de naissance",
 index_desc="Pourquoi le tronc du jour représente le « moi » et quels sont les dix Troncs célestes.",
 lead="Parmi les quatre piliers d'un thème de naissance Saju, le pilier du jour est le plus personnel : il ne dépend que de ton jour de naissance. Tu lis ici ce que signifie Ilju, ce que le tronc du jour représente traditionnellement et comment l'utiliser pour ton profil.",
 body='''<h2>Qu'est-ce que le pilier du jour ?</h2>
<p>Le thème de naissance Saju se compose de quatre piliers : année, mois, jour et heure. Chaque pilier a deux signes, en haut un <strong>Tronc céleste</strong> et en bas une <strong>Branche terrestre</strong>. Le pilier du jour s'appelle <em>Ilju</em> (일주, 日柱) en coréen. Il se calcule à partir du jour du calendrier, non de l'année de naissance, et se répète selon un rythme fixe de 60 jours.</p>

<h2>Pourquoi le tronc du jour représente-t-il le « moi » ?</h2>
<p>Le signe supérieur du pilier du jour, le <strong>tronc du jour</strong> (일간, 日干), est considéré dans l'enseignement classique comme le point de repère de tout le thème de naissance. Tous les autres signes se lisent par rapport à lui : qu'est-ce qui le nourrit, qu'est-ce qui le met au défi, qu'est-ce qui lui ressemble ? C'est pourquoi on dit souvent, en raccourci, dans le Saju que le tronc du jour est « toi-même ». C'est une image traditionnelle, pas une mesure.</p>

<h2>Les dix Troncs célestes</h2>
<p>Il y a dix troncs : un signe Yang et un signe Yin pour chacun des cinq éléments.</p>
<table class="t"><tr><th>Tronc</th><th>Coréen</th><th>Élément</th><th>Polarité</th></tr>
<tr><td>甲</td><td>gap (갑)</td><td>Bois</td><td>Yang</td></tr>
<tr><td>乙</td><td>eul (을)</td><td>Bois</td><td>Yin</td></tr>
<tr><td>丙</td><td>byeong (병)</td><td>Feu</td><td>Yang</td></tr>
<tr><td>丁</td><td>jeong (정)</td><td>Feu</td><td>Yin</td></tr>
<tr><td>戊</td><td>mu (무)</td><td>Terre</td><td>Yang</td></tr>
<tr><td>己</td><td>gi (기)</td><td>Terre</td><td>Yin</td></tr>
<tr><td>庚</td><td>gyeong (경)</td><td>Métal</td><td>Yang</td></tr>
<tr><td>辛</td><td>sin (신)</td><td>Métal</td><td>Yin</td></tr>
<tr><td>壬</td><td>im (임)</td><td>Eau</td><td>Yang</td></tr>
<tr><td>癸</td><td>gye (계)</td><td>Eau</td><td>Yin</td></tr></table>

<h2>Et la branche du jour ?</h2>
<p>Sous le tronc se trouve la branche du jour, l'un des douze animaux. Elle se lit traditionnellement comme l'environnement dans lequel vit le « moi », et elle est souvent aussi associée à la vie de couple et à la proximité. Les animaux existants sont expliqués dans <a href="{L:ddi}">Signe du zodiaque coréen (Ddi)</a>.</p>

<h2>Pourquoi ne peux-tu pas calculer rapidement ton Ilju toi-même ?</h2>
<p>Les jours suivent un cycle continu de 60 combinaisons qui ne se règle ni sur les mois ni sur les années. Il faut pour cela une table de calendrier ou un calcul à partir d'un jour de départ connu. De plus, un jour Saju ne commence pas à la même heure selon toutes les méthodes, ce qui peut jouer pour les naissances autour de minuit. Pour être sûr(e), fais calculer ton profil et vérifie l'heure de naissance.</p>

<h2>Comment lit-on le pilier du jour ?</h2>
<p>Pris seul, le tronc du jour dit peu de choses. Ce n'est qu'avec les autres piliers qu'une image apparaît, par exemple quels <a href="{L:elements}">cinq éléments</a> sont fortement ou faiblement présents. Plus d'informations sur la structure dans <a href="{L:pillars}">Les quatre piliers du Saju</a>.</p>'''),
"pillars": dict(
 title="Les quatre piliers du Saju : année, mois, jour et heure", h1="Les quatre piliers du Saju expliqués",
 desc="Que sont les quatre piliers (Saju, 사주) et les huit signes (Palja, 팔자) ? Structure, Troncs célestes, Branches terrestres et ce que décrivent traditionnellement les piliers de l'année, du mois, du jour et de l'heure.",
 index_title="Les quatre piliers du Saju : année, mois, jour et heure",
 index_desc="Quatre piliers, huit signes : la structure expliquée pas à pas.",
 lead="Saju signifie littéralement « quatre piliers ». Chaque pilier a deux signes, ce qui fait huit signes : le Palja. Cet article explique la structure pas à pas.",
 body='''<h2>Quatre piliers, huit signes</h2>
<p>Le <em>Saju</em> coréen (사주, 四柱) signifie « quatre piliers ». Il s'agit de l'année, du mois, du jour et de l'heure de naissance. Chaque pilier se compose d'un <strong>Tronc céleste</strong> (en haut) et d'une <strong>Branche terrestre</strong> (en bas). Quatre piliers fois deux signes donnent huit signes, en coréen <em>Palja</em> (팔자).</p>

<h2>Troncs célestes et Branches terrestres</h2>
<ul>
<li><strong>Dix Troncs célestes :</strong> 甲 乙 丙 丁 戊 己 庚 辛 壬 癸. Deux appartiennent à chacun des cinq éléments, une fois Yang, une fois Yin.</li>
<li><strong>Douze Branches terrestres :</strong> 子 丑 寅 卯 辰 巳 午 未 申 酉 戌 亥. Ce sont les douze animaux, du Rat au Cochon.</li>
</ul>
<p>Le tronc et la branche sont combinés en une paire qui suit un cycle de 60 combinaisons. 2027 est par exemple 丁未.</p>

<h2>Ce que les quatre piliers décrivent traditionnellement</h2>
<table class="t"><tr><th>Pilier</th><th>Association traditionnelle</th></tr>
<tr><td>Année</td><td>Origine, famille, environnement extérieur</td></tr>
<tr><td>Mois</td><td>Foyer parental, métier, entourage à l'âge adulte ; considéré comme particulièrement formateur</td></tr>
<tr><td>Jour</td><td>Le moi ; le signe supérieur est le « maître du jour »</td></tr>
<tr><td>Heure</td><td>Vie intérieure, dernières années, effet vers l'extérieur</td></tr></table>
<p>C'est une attribution classique servant de cadre de réflexion. Elle ne dit rien sur le déroulement réel d'une vie.</p>

<h2>Pourquoi l'heure de naissance est importante</h2>
<p>Sans heure de naissance, le pilier de l'heure ne peut pas être déterminé ; on travaille alors avec trois piliers. De plus, le mois Saju ne commence pas le premier du mois civil, mais à des points solaires (les « termes solaires »). C'est pourquoi le thème de naissance peut différer de la date du calendrier courant, surtout autour du changement de mois.</p>

<h2>Pour aller plus loin</h2>
<p>Tu trouveras les éléments de base des signes dans <a href="{L:elements}">Les cinq éléments du Saju</a> et <a href="{L:yinyang}">Yin et Yang dans le Saju</a>.</p>'''),
"yinyang": dict(
 title="Yin et Yang dans le Saju : la signification de la polarité", h1="Yin et Yang dans le Saju",
 desc="Yin et Yang dans le Saju expliqués simplement : comment chacun des cinq éléments apparaît sous deux formes, quels Troncs célestes sont Yin et Yang et comment s'en servir comme modèle de réflexion.",
 index_title="Yin et Yang dans le Saju : la signification de la polarité",
 index_desc="Comment chacun des cinq éléments apparaît sous une forme Yang et une forme Yin.",
 lead="Yin et Yang ne sont pas un schéma bien-mal, mais deux formes d'apparition de la même chose. Dans le Saju, chacun des cinq éléments reçoit une forme Yang et une forme Yin.",
 body='''<h2>Deux formes par élément</h2>
<p>Les dix Troncs célestes naissent du fait que chacun des cinq éléments apparaît deux fois : une fois comme Yang (vers l'extérieur, ouvert, puissant), une fois comme Yin (vers l'intérieur, fin, condensé).</p>
<table class="t"><tr><th>Élément</th><th>Yang</th><th>Yin</th></tr>
<tr><td>Bois</td><td>甲 (grand arbre)</td><td>乙 (herbe, fleur)</td></tr>
<tr><td>Feu</td><td>丙 (soleil)</td><td>丁 (flamme de bougie)</td></tr>
<tr><td>Terre</td><td>戊 (montagne)</td><td>己 (champ)</td></tr>
<tr><td>Métal</td><td>庚 (hache, épée)</td><td>辛 (bijou, aiguille)</td></tr>
<tr><td>Eau</td><td>壬 (mer, fleuve)</td><td>癸 (pluie, rosée)</td></tr></table>
<p>Les images entre parenthèses sont les aide-mémoire habituels de la tradition. Elles aident à retenir, ce ne sont pas des descriptions de caractère figées.</p>

<h2>Yin et Yang dans les années</h2>
<p>Les années aussi sont Yin ou Yang. Les années qui se terminent par un chiffre pair portent des troncs Yang (2026 : 丙, Feu Yang). Les années qui se terminent par un chiffre impair sont Yin (2027 : 丁, Feu Yin). C'est pourquoi on décrit souvent 2026 comme un « feu ouvert » et 2027 comme un « feu plus discret ». Voir à ce sujet <a href="{L:sheep}">L'année de la Chèvre de feu 2027</a>.</p>

<h2>Comment l'utiliser</h2>
<p>Sous forme de question : où, dans ma vie, puis-je aller vers l'extérieur en ce moment, et où plutôt vers l'intérieur ? Ce n'est qu'un modèle de réflexion et cela ne remplace aucun conseil.</p>'''),
}
