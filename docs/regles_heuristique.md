# Règles de l'heuristique (approche A)

Pour cette première version les poids sont calculés sur l'échantillon NHTSA de 1000 lignes (996 plaintes) et seront recalculés ensuite sur le fichier complet.

## Principe

Des règles attribuent un poids à une cause selon les symptômes que l'utilisateur a cochés. Les poids sont ensuite additionnés, puis les causes sont classées par score.
Chaque règle a une source, et on peut dire pourquoi chaque score est ce qu'il est.

- Cause : une des 15 causes du document des libellés (C1 à C15, fichier `bdd/donnees/cause.csv`). Chaque cause est
  reliée à une ou plusieurs catégories de composants NHTSA par la table `cause_composant`
  (fichier `bdd/donnees/cause_composant.csv`) : c'est ce lien qui permet de compter les plaintes d'une cause.
- Symptôme : un des 10 symptômes du document des libellés (S1 à S10).
- Entrées : les symptômes cochés, le carburant et la boîte saisis dans le formulaire. L'heuristique n'utilise pas le
  texte libre (réservé à l'approche B). Le carburant et la boîte ne sont pas dans les données NHTSA : ils servent
  seulement à écarter les causes qui ne concernent pas la voiture (voir « Filtres carburant et boîte »).
- Sortie : une liste de causes classées avec un score de confiance relatif, qui totalise 100 %. Ce n'est pas une
  probabilité au sens statistique.

## Mots clés

| N° | Symptôme (libellé français) | Mots-clés anglais | Mot de contexte |
|---|---|---|---|
| S1 | La voiture démarre difficilement ou pas du tout | `fail* to start`, `not start`, `no start`, `hard start`, `slow crank`, `no crank` | aucun |
| S2 | Le voyant moteur est allumé | `check engine`, `engine light`, `malfunction indicator`, `dtc` | aucun |
| S3 | Perte de puissance quand j'accélère | `stall*`, `loss of power`, `lost power`, `hesitat*`, `lag in`, `loss of acceleration`, `reduced power` | aucun |
| S4 | Bruit métallique ou grincement au freinage | `grind*`, `squeal*`, `squeak*`, `screech*`, `noise` | `brake` |
| S5 | La pédale de frein est molle ou s'enfonce trop | `spongy`, `soft pedal`, `pedal to the floor`, `brake fluid`, `brakes failed`, `not brake`, `loss of brak*` | aucun |
| S6 | La direction est dure ou fait du bruit | `power steering`, `hard to steer`, `difficult to steer`, `steering wheel locked`, `steering became stiff`, `stiff steering`, `heavy steering` | aucun |
| S7 | Vibrations dans le volant ou dans la voiture | `vibrat*`, `shak*`, `shudder*`, `wobbl*` | aucun |
| S8 | Fumée ou odeur de brûlé | `smoke`, `smoking`, `burning smell`, `burnt smell`, `smell of burning`, `burning odor`, `burning oil` | aucun |
| S9 | Le moteur chauffe (voyant de température) | `coolant`, `head gasket`, `engine overheat*`, `overheating engine`, `temperature gauge`, `overheat*` | aucun |
| S10 | Les vitesses passent mal (à-coups, la voiture patine) | `hard shift*`, `harsh shift*`, `shifting`, `jerk*`, `slipping`, `transmission slip*`, `clutch` | aucun |

- `*` en fin de mot = début de mot (`vibrat*` repère vibration, vibrating).
- Mot de contexte : il doit aussi apparaître dans le texte (ex. `brake` pour « bruit au freinage »).
- Mots-clés écrits sans apostrophe : le fichier contient des caractères abîmés (`wasnât`).

## Comment les poids sont calculés

1. Le texte de chaque plainte (`CDESCR`) est mis en minuscules. Les mots-clés associés à chaque symptôme sont ensuite recherchés dans le texte (voir mots-clés ci-dessus).
2. Pour ces plaintes, on regarde leurs composants (`COMPDESC`), regroupés en catégorie : la partie avant le premier `:`, comme dans l'ingestion (`SERVICE BRAKES` et `SERVICE BRAKES, HYDRAULIC` restent deux catégories différentes).
3. Une règle relie un symptôme à une cause seulement si le document des libellés les relie (colonne « Symptômes » des causes).
4. Poids = part des plaintes du symptôme dont au moins une catégorie appartient à la cause, en pourcentage arrondi.
   Exemple : parmi les 50 plaintes « le moteur chauffe », 27 ont une catégorie de la cause C4 (`ENGINE AND ENGINE COOLING` ou `ENGINE`), soit 54.
5. Une règle qui repose sur moins de 3 plaintes n'est pas conservée. Les poids d'un symptôme ne totalisent donc pas 100.
6. Un symptôme avec moins de 20 plaintes n'a **pas de règle** pour l'instant (fiabilité insuffisante).

## Table de règles

Source de toutes les lignes : échantillon NHTSA 2025-2026, 1000 lignes (996 plaintes).
« Plaintes » = plaintes de la cause / plaintes repérées pour le symptôme.
Fiabilité : *moyenne* à partir de 90 plaintes repérées, *faible* de 20 à 89, *insuffisante* en dessous.

| Symptôme | Cause | Poids | Plaintes | Fiabilité |
|---|---|---|---|---|
| S2. Voyant moteur | C15. Sonde lambda défaillante | 63 | 61 / 97 | moyenne |
| S2. Voyant moteur | C3. Bougies ou bobines d'allumage usées | 56 | 54 / 97 | moyenne |
| S2. Voyant moteur | C12. Fuite d'huile moteur | 56 | 54 / 97 | moyenne |
| S2. Voyant moteur | C7. Bougies de préchauffage défaillantes | 51 | 49 / 97 | moyenne |
| S2. Voyant moteur | C8. Filtre à particules encrassé | 51 | 49 / 97 | moyenne |
| S2. Voyant moteur | C9. Vanne EGR encrassée | 51 | 49 / 97 | moyenne |
| S2. Voyant moteur | C1. Batterie faible ou défaillante | 5 | 5 / 97 | moyenne |
| S2. Voyant moteur | C13. Alternateur défaillant | 5 | 5 / 97 | moyenne |
| S3. Perte de puissance | C15. Sonde lambda défaillante | 48 | 52 / 108 | moyenne |
| S3. Perte de puissance | C3. Bougies ou bobines d'allumage usées | 41 | 44 / 108 | moyenne |
| S3. Perte de puissance | C8. Filtre à particules encrassé | 34 | 37 / 108 | moyenne |
| S3. Perte de puissance | C9. Vanne EGR encrassée | 34 | 37 / 108 | moyenne |
| S3. Perte de puissance | C5. Embrayage usé | 15 | 16 / 108 | moyenne |
| S3. Perte de puissance | C6. Boîte automatique défaillante | 15 | 16 / 108 | moyenne |
| S6. Direction dure | C10. Direction assistée défaillante | 51 | 20 / 39 | faible |
| S7. Vibrations | C2. Plaquettes ou disques de frein usés | 11 | 5 / 46 | faible |
| S8. Fumée ou odeur de brûlé | C4. Problème de refroidissement du moteur | 38 | 9 / 24 | faible |
| S8. Fumée ou odeur de brûlé | C12. Fuite d'huile moteur | 38 | 9 / 24 | faible |
| S8. Fumée ou odeur de brûlé | C8. Filtre à particules encrassé | 29 | 7 / 24 | faible |
| S8. Fumée ou odeur de brûlé | C9. Vanne EGR encrassée | 29 | 7 / 24 | faible |
| S8. Fumée ou odeur de brûlé | C5. Embrayage usé | 21 | 5 / 24 | faible |
| S9. Le moteur chauffe | C4. Problème de refroidissement du moteur | 54 | 27 / 50 | faible |
| S10. Les vitesses passent mal | C5. Embrayage usé | 45 | 27 / 60 | faible |
| S10. Les vitesses passent mal | C6. Boîte automatique défaillante | 45 | 27 / 60 | faible |

**Symptômes sans règle (en attente du fichier complet)** : S1. Démarre difficilement (14 plaintes repérées),
S4. Bruit au freinage (3), S5. Pédale de frein molle (10). Le freinage est presque absent de l'échantillon.
La règle S7 → C11 (pneus et roues) n'est pas conservée : 1 seule plainte.

**Limites connues** :
- Des causes qui partagent la même catégorie ont le même poids (par exemple C7, C8 et C9 pour S2, toutes
  reliées à `ENGINE`). Le comptage seul ne les départage pas : ce sont les autres symptômes cochés et les filtres
  carburant et boîte qui font la différence.
- Le diesel est presque absent des plaintes américaines (`FUEL SYSTEM, DIESEL` : 1 plainte dans l'échantillon).
  Les poids de C7, C8 et C9 viennent surtout de la catégorie `ENGINE`, qui regroupe des voitures essence.

## Filtres carburant et boîte

Avant le calcul, les causes qui ne concernent pas la voiture sont écartées, d'après les colonnes `carburant` et
`boite` de la table `cause` :

| Règle | Condition | Effet |
|---|---|---|
| E1 | carburant = diesel | C3 (bougies d'allumage) est écartée |
| E2 | carburant = essence | C7, C8 et C9 (causes diesel) sont écartées |
| E3 | boîte = automatique | C5 (embrayage) est écartée |
| E4 | boîte = manuelle | C6 (boîte automatique) est écartée |

Si le carburant ou la boîte n'est pas renseigné, aucune cause n'est écartée pour ce critère.

Les règles diesel D1 à D3 (diesel + S1 → C7 ; diesel + S2 ou S3 → C8 et C9 ; diesel + S8 → C8 et C9) sont
couvertes par la table de règles : C7, C8 et C9 n'y apparaissent qu'avec ces symptômes, et les filtres les
écartent pour une voiture essence. La règle D1 (S1 → C7) attend le fichier complet, comme tout le symptôme S1.

## Algorithme

1. Récupérer les symptômes cochés. Ceux qui n'ont pas de règle sont ignorés.
2. Écarter les causes qui ne correspondent pas au carburant ou à la boîte saisis (règles E1 à E4).
3. Pour chaque règle d'un symptôme coché dont la cause n'est pas écartée, ajouter son **poids** au score de la cause.
4. Calculer le score affiché : `score de la cause ÷ somme des scores × 100`, arrondi à l'entier.
5. Classer les causes par score décroissant. En cas d'égalité : le plus grand nombre de plaintes sous-jacentes
   (somme de la colonne « Plaintes »), puis l'ordre des identifiants (C1, C2…).
6. Pour chaque cause classée, chercher les problèmes connus **du véhicule choisi** liés aux catégories de la cause.
7. Remplir l'explication : quels symptômes ont apporté combien de points à la cause, et combien de signalements
   existent pour ce véhicule et ces catégories.

### Exemple chiffré

Voiture essence, boîte manuelle. L'utilisateur coche « Perte de puissance » (S3) et « Les vitesses passent mal » (S10).

C6 est écartée (boîte manuelle), C8 et C9 sont écartées (essence).

| Cause | Points de S3 | Points de S10 | Score | Score affiché |
|---|---|---|---|---|
| C5. Embrayage usé | 15 | 45 | 60 | **40 %** |
| C15. Sonde lambda défaillante | 48 | | 48 | 32 % |
| C3. Bougies ou bobines d'allumage usées | 41 | | 41 | 28 % |

Somme des scores : 60 + 48 + 41 = 149, donc C5 = 60 ÷ 149 = 40 %. Avec une boîte automatique, C6 prendrait la
place de C5 avec les mêmes points.

## Cas limites

- **Aucun symptôme coché, ou seulement des symptômes sans règle** : aucune règle ne s'applique, le résultat est une
  liste vide (réponse `200` avec `"resultats": []`, pas une erreur).
- **Carburant ou boîte non renseignés** : aucune cause n'est écartée pour ce critère.
- **`description`** : ignorée par l'heuristique (réservée à l'approche B).
- **Véhicule** : les poids sont calculés à partir des données de tous les véhicules. Le véhicule sélectionné sert ensuite à rechercher les problèmes qui lui sont associés.
- **Aucun problème connu pour ce véhicule et cette cause** : la cause apparaît dans le classement, mais aucun problème n'est associé.
- **Égalité de scores** : règle de l'étape 5 de l'algorithme.

## Complexité

Soit s le nombre de symptômes sélectionnés, avec un maximum de 10, k le nombre de règles par symptôme, avec un maximum de 8, et c le nombre de causes différentes obtenues, avec un maximum de 15.

- Le filtrage carburant et boîte est en O(c).
- Le calcul des scores est en O(s × k).
- Le classement des causes est en O(c log c).
- Le calcul des scores ne dépend pas directement du nombre de plaintes présentes dans la base, car les poids sont calculés à l'avance.
- La recherche des problèmes associés au véhicule dépend de la base de données. Les index prévus sur probleme_composant et vehicule_probleme permettent de faciliter cette recherche.
