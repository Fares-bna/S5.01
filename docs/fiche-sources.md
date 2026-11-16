# Fiche des sources et vérification des données

Nous allons utiliser un premier jeu de données issu du National Highway Traffic Safety Administration (NHTSA).

Nous nous concentrons sur le dataset des plaintes, qui va permettre d'alimenter par la suite nos deux systèmes de recommandation.

La version sur laquelle nous nous appuyons est la suivante :

| Path | Size | Updated |
|---|---|---|
| COMPLAINTS_RECEIVED_2025-2026.zip | 41 MB | 11/04/2026 04:27:08 AM ET |

Empreinte sha256 du zip téléchargé le 4 novembre 2026 : `6a106e8509b917c557c7eef257c2c77edf3056b6271a585e6f1b9ce53211a7d0` (vérifiée le 12 novembre). Le zip est déposé sur le Drive de l'équipe ; le fichier brut n'est jamais versionné dans git (`data/nhtsa/` est ignoré).

Nous y ajoutons une vérification du fichier suivant, qui recense toutes les colonnes, afin de s'assurer que notre version actuelle correspond aux mêmes critères qu'il y a 5 ans.

| Path | Size | Updated |
|---|---|---|
| CMPL.txt | 10 KB | 05/01/2026 09:46:45 AM ET |

Une décision d'ingestion a été prise. Deux choix s'offraient à nous : utiliser le jeu FLAT_CMPL.zip (358 Mo), données saisies depuis le 1er janvier 1995, ou sélectionner les trois fichiers 2015-2019, 2020-2024 et 2025-2026 (environ 190 Mo), soit les dernières années.

Pour des raisons de praticité, et dans l'optique de tester avant d'agrandir notre champ plus tard pour de potentielles améliorations du projet, la deuxième option est maintenue. À ce jour, seul le fichier 2025-2026 est téléchargé, vérifié et chargé en base ; les deux autres (2015-2019 et 2020-2024) ne sont pas chargés.

## Quelques remarques

### 1. Identifier une plainte : CMPLID et ODINO

CMPLID est le numéro interne unique de chaque ligne. Dans le fichier téléchargé le 4 nov 2026 (COMPLAINTS_RECEIVED_2025-2026.zip), il est unique sur les 210 698 lignes. Selon le dictionnaire officiel (CMPL.txt), NHTSA peut modifier les données d'un CMPLID d'un jour à l'autre, et le fichier est mis à jour tous les jours. Si on recharge un fichier plus récent, il faut donc mettre à jour les lignes existantes au lieu d'en ajouter : le chargement est conçu ainsi (`ON CONFLICT`, une seule transaction), et il a été rejoué deux fois sans créer de doublon. Pour le projet, on garde la version téléchargée le 4 nov, avec son empreinte sha256.

ODINO est le numéro de référence de la plainte. Il se répète quand une plainte touche plusieurs composants : on a 141 126 plaintes pour 210 698 lignes.

**Décision (validée avec Fares)** : une ligne par composant. D'une voiture à une autre, une même plainte peut ne pas concerner les mêmes composants. En base, une plainte (table `probleme`) est donc reliée à un ou plusieurs composants (table `probleme_composant`).

### 2. Colonnes inutilisables car vides : TRANS_TYPE, FUEL_TYPE, VEHICLE_OPERATOR

TRANS_TYPE est le type de boîte de vitesses (auto ou manuelle), et FUEL_TYPE le type de carburant (essence, diesel, hybride...). Ils sont vides à 100 % dans ce fichier, donc inutilisables. Dans le formulaire de l'appli, la boîte et le carburant restent facultatifs, mais ils ne servent pas à filtrer les plaintes. En base, les colonnes carburant, boîte et cylindres du véhicule sont à NULL.

Le problème : une voiture automatique ou manuelle ne présente pas les mêmes problèmes (« maladies », symptômes, etc.), et essence et diesel sont deux moteurs différents, avec des composants en plus ou en moins selon le type. Le fichier NHTSA ne permet pas de faire cette distinction. Trois pistes ont été étudiées :

**→ Piste 1 : décoder le VIN (vPIC).** Elle donnerait le carburant, la boîte et les cylindres de chaque voiture. **Non réalisée** : le VIN est partiel (11 caractères) et le taux de réussite du décodage n'a pas été mesuré. Si elle est menée, ce sera progressivement (3 VIN, puis 17, puis le fichier entier), avec un seuil de réussite proposé de 70 % de carburants retrouvés.

**→ Piste 1 bis : une autre base de caractéristiques.** On relierait à nos plaintes un second jeu de données qui décrit les modèles (par exemple « Toyota Corolla 2019 : essence, boîte automatique, 4 cylindres »), avec la marque, le modèle et l'année comme clé. **Non utilisée.** Elle serait moins précise, parce qu'un même modèle peut avoir plusieurs moteurs. Deux jeux ont été repérés, sans évaluation détaillée :

- fueleconomy.gov (EPA, États-Unis) : fichier CSV de tous les véhicules 1984–2026, mis à jour le 16 juin 2026. La page ne liste ni les colonnes ni la licence.
- ADEME (data.gouv.fr) : émissions de CO2 et de polluants des véhicules commercialisés en France, Licence Ouverte, mis à jour le 15 décembre 2025, avec marque, modèle et type d'énergie. La boîte de vitesses et la cylindrée ne sont pas mentionnées, et elle ne couvre que les véhicules neufs vendus en France.

**→ Piste 2 : règles de l'heuristique.** L'utilisateur choisit le carburant et la boîte dans le formulaire, et les règles de l'approche A en tiennent compte (essence : bougies d'allumage ; diesel : bougies de préchauffage, filtre à particules, vanne EGR ; boîte manuelle : embrayage, synchroniseurs ; boîte automatique : patinage, convertisseur de couple). Elle ne dépend pas des données NHTSA et fonctionne pour toutes les voitures. Ce sont des règles d'expert, pas des résultats statistiques : on les limite à une dizaine de règles, chacune avec sa source (L'argus, goodmecano.com, auto-max.fr, colonne « source » du tableau), validées par l'équipe, puis testées sur le jeu de test séparé. Les règles diesel ne vivent que dans l'heuristique, et leur poids est fixé par l'équipe, pas par la fréquence des plaintes. Limites : rien n'est vérifié pour les voitures hybrides et électriques, et ces règles ne peuvent pas être évaluées sur NHTSA dans le benchmark, puisque le carburant n'y figure pas.

**Décision pour le rendu 1 : la piste 2 seulement.** Ses règles (`docs/regles_heuristique.md`) alimentent l'approche A de l'API. Les pistes 1 et 1 bis restent des axes d'amélioration.

**Limite : marques françaises absentes.** Les plaintes NHTSA couvrent le marché américain, sans Peugeot, Renault ni Citroën. On y remédie en limitant l'approche B aux marques présentes des deux côtés, et en gardant l'heuristique pour toutes les autres.

C'est un point faible, que nous assumons : beaucoup de marques vendues en France sont dans NHTSA (Toyota, Volkswagen, BMW, Mercedes, Audi, Nissan, Ford, Hyundai, Kia), donc le projet reste utile pour une grande partie des voitures françaises. Aucune source de plaintes européenne équivalente n'a été identifiée pour Peugeot, Renault et Citroën. On en fait un axe d'amélioration : permettre à des retours français d'exister.

Pour la soutenance : le dire nous-mêmes avant qu'on nous le demande : « nos données couvrent le marché américain, voilà la limite, voilà comment on la gère ».

VEHICLE_OPERATOR est le nom du conducteur. Il est vide aussi, mais on l'exclut quand même, car c'est une donnée personnelle.

### 3. Colonnes à exclure car elles identifient quelqu'un : VIN et DEALER_NAME

VIN est le numéro d'identification du véhicule. Il est rempli à environ 98 % (c'est un numéro partiel de 11 caractères, sans le numéro de série). Complet, il permettrait de retrouver un véhicule précis ; ici il est partiel, mais on l'exclut par précaution : il n'est jamais lu ni stocké (seules 15 colonnes utiles sont lues). Si la piste 1 est menée plus tard, le VIN ne servira qu'une fois, en mémoire, à l'ingestion pour décoder le carburant, la boîte et les cylindres, puis il sera abandonné sans être écrit en base.

**RGPD** : la plaque d'immatriculation n'est pas retenue pour le rendu 1. Elle est rattachée à un titulaire, et marque, modèle et année suffisent à notre besoin : l'utilisateur saisit donc ces trois informations à la place. La plaque reste un axe d'amélioration (pour pré-remplir le véhicule), à traiter avec précaution.

DEALER_NAME est le nom du concessionnaire. Il est vide à 91 %, et on l'exclut aussi (comme les autres colonnes DEALER_ et CITY).

### 4. Relier une plainte à une pièce de la voiture : COMPDESC

COMPDESC est le composant concerné par la plainte (ENGINE, ELECTRICAL SYSTEM, POWER TRAIN, STEERING, SERVICE BRAKES...). Il est rempli partout. C'est lui qui sert à relier les causes aux composants dans la table de Fares (table causes ↔ composants, PR #10). Environ 10 % des lignes sont « UNKNOWN OR OTHER », donc inutilisables pour ça : ces plaintes sont gardées, mais sans lien vers un composant. La catégorie du composant est la partie avant le premier « : » (les variantes ne sont pas fusionnées).

### 5. Le texte que l'approche B va lire : CDESCR

CDESCR est le texte de la plainte écrit par le propriétaire, en anglais, avec une longueur médiane d'environ 600 caractères. C'est ce texte que l'approche B transformera en vecteurs. La plus longue fait 2 132 caractères, plus que les 2 048 annoncés, donc le champ en base doit être un TEXT sans limite.

Remarque : le texte libre peut rarement contenir un identifiant que le propriétaire a tapé lui-même. Les numéros de téléphone sont masqués à l'ingestion, mais le reste du texte n'est pas nettoyé. À signaler comme limite, pas comme une raison de bloquer l'échantillon.

## 6. Causes et symptômes : hors de cette fiche

Cette fiche ne couvre que les données NHTSA. NHTSA ne fournit ni causes, ni solutions, ni liste de symptômes : ils sont rédigés à la main, avec leurs sources, dans la tâche de Fares (« Libellés symptômes, causes, solutions, sources »). Les 15 causes (C1 à C15) et leurs liens avec les composants NHTSA sont documentés dans `docs/fiche-table-causes-composants.md`.

## 7. Vérification et chargement des données

**Validation du format (pandera)** : avant toute transformation, le fichier lu est contrôlé : CMPLID numérique et unique, ODINO numérique, année sur 4 chiffres, CRASH / FIRE / MEDICAL_ATTN en Y/N, VEHICLES_TOWED_YN en Y/N/vide, INJURED et DEATHS numériques, date LDATE valide, PROD_TYPE sur une lettre, fichier non vide. Si un contrôle échoue, l'ingestion s'arrête avec un message lisible.

**Règles de nettoyage** :
- seuls les véhicules sont gardés (PROD_TYPE = V) ;
- les plaintes dont le texte est vide ou sans information (« N/A », « Unknown », « None », « . », etc.) sont écartées ;
- l'année 9999 est remplacée par NULL ;
- les numéros de téléphone sont masqués ;
- le VIN n'est jamais lu.

**Choix de traitement** :
- gravité : `critique` si décès ; `elevee` si blessés, soins médicaux, incendie ou accident ; `moderee` si remorquage ; `faible` sinon ;
- un véhicule est identifié par 6 colonnes (marque, modèle, année, carburant, boîte, cylindres), prêtes pour un futur décodage du VIN ;
- le chargement se fait en une seule transaction et peut être rejoué sans doublon.

**Chiffres chargés** :

| | Fichier complet 2025-2026 | Échantillon |
|---|---|---|
| Lignes lues | 210 698 | – |
| Plaintes | 140 271 | 996 |
| Composants | 503 | 67 |
| Véhicules | 7 360 | 674 |
| Liens plainte-composant | 186 665 | 905 |
| Liens véhicule-plainte | 140 271 | – |

Les plaintes chargées vont du 2025-01-01 au 2026-11-02.

## 8. Limites et pistes

**Limites** :
- carburant, boîte et cylindres sont à NULL (décodage du VIN non fait) ;
- seul le fichier 2025-2026 est chargé (2015-2019 et 2020-2024 non chargés) ;
- le diesel est très peu présent dans NHTSA ;
- les marques françaises sont absentes (voir point 2) ;
- le texte libre n'est nettoyé que pour les téléphones (point 5) ;
- les causes, symptômes et solutions ne viennent pas de NHTSA (section 6).

**Pistes (hors rendu 1)** :
- test de décodage du VIN avec vPIC (lots de 50, seuil proposé de 70 % de carburant), à mesurer ;
- champ plaque d'immatriculation ;
- RappelConso (licence Etalab 2.0 selon Fares, à vérifier ; nombre de fiches voitures à compter) ;
- base britannique MOT : ce sont des défauts relevés par des inspecteurs, pas des symptômes décrits par un conducteur, donc axe d'amélioration seulement ;
- chargement des deux autres fichiers NHTSA.
