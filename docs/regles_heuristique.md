# Règles de l'heuristique (approche A)

Pour cette première version les poids sont calculés sur l'échantillon NHTSA de 1000 plaintes et seront recalculés ensuite sur le fichier complet.

## Principe

Des règles attribuent un poids à une cause selon les symptômes que l'utilisateur a cochés. Les poids sont ensuite additionnés, puis les causes sont classées par score. 
Chaque règle a une source, et on peut dire pourquoi chaque score est ce qu'il est.

- Cause : dans cette version, une cause est un **composant NHTSA regroupé** (`ENGINE`, `ELECTRICAL SYSTEM`...).
  Les données ne permettent pas d'être plus précis (batterie, bougies, alternateur). *À confirmer avec Fares.*
- Entrées : les symptômes cochés. L'heuristique n'utilise pas le texte libre (réservé à l'approche B) ni
  `carburant` et `boite`, vides dans les données NHTSA.
- Sortie : une liste de causes classées avec un score de confiance relatif, qui totalise 100 %. Ce n'est pas une
  probabilité au sens statistique.

## Mots clés

| N° | Symptôme (libellé français) | Mots-clés anglais | Mot de contexte |
|---:|---|---|---|
| 1 | Bruit au freinage | `grind*`, `squeal*`, `squeak*`, `screech*`, `noise` | `brake` |
| 2 | Pédale de frein molle ou qui s'enfonce | `spongy`, `soft pedal`, `pedal to the floor`, `brake fluid`, `brakes failed`, `not brake`, `loss of brak*` | aucun |
| 3 | Vibrations au freinage | `vibrat*`, `shak*`, `shudder*`, `pulsat*`, `wobbl*` | `brake` |
| 4 | Voyant de frein, ABS ou contrôle de stabilité allumé | `abs`, `esc service`, `stability control`, `traction control`, `brake warning` | aucun |
| 5 | Voyant moteur allumé | `check engine`, `engine light`, `malfunction indicator`, `dtc` | aucun |
| 6 | Difficulté au démarrage | `fail* to start`, `not start`, `no start`, `hard start`, `slow crank` | aucun |
| 7 | Perte de puissance ou calage | `stall*`, `loss of power`, `lost power`, `hesitat*`, `lag in` | aucun |
| 8 | Surchauffe ou liquide de refroidissement bas | `coolant`, `head gasket`, `engine overheat*`, `overheating engine`, `temperature gauge` | aucun |
| 9 | Batterie ou alternateur défaillant | `dead battery`, `battery drain*`, `battery died`, `battery fail*`, `battery replace*`, `new battery`, `alternator`, `jump start*` | aucun |
| 10 | Éclairage qui clignote ou s'éteint | `flicker*`, `lights went out`, `lights go out`, `headlight*`, `headlamp*` | aucun |

- `*` en fin de mot = début de mot (`vibrat*` repère vibration, vibrating).
- Mot de contexte : il doit aussi apparaître dans le texte (ex. `brake` pour « bruit au freinage »).
- Mots-clés écrits sans apostrophe : le fichier contient des caractères abîmés (`wasnât`).

## Comment les poids sont calculés

1. Le texte de chaque plainte (`CDESCR`) est mis en minuscules.Les mots-clés associés à chaque symptôme sont ensuite recherchés dans le texte. (voir mots cles ci-dessus).
2. Pour ces plaintes, on regarde leur composant (`COMPDESC`), regroupé avant le premier `:` ou `,`.
3. Poids = part des plaintes du symptôme qui concernent ce composant, en pourcentage arrondi.
   Exemple : parmi les 38 plaintes « surchauffe », 20 concernent `ENGINE`, soit 53.
4. Pour chaque symptôme, on conserve au maximum 3 composants ayant au moins 3 plaintes. Le composant `UNKNOWN OR OTHER` n'est pas conservé car il ne permet pas d'identifier une cause précise.Les poids retenus ne totalisent donc pas 100
5. Un symptôme avec moins de 20 plaintes n'a **pas de règle** pour l'instant (fiabilité insuffisante).


## Table de règles

Source de toutes les lignes : échantillon NHTSA 2025-2026, 1000 lignes (998 plaintes).
« Plaintes » = plaintes du composant / plaintes repérées pour le symptôme.
Fiabilité : *moyenne* à partir de 90 plaintes repérées, *faible* de 20 à 89, *insuffisante* en dessous.

| Symptôme | Cause (composant NHTSA) | Poids | Plaintes | Fiabilité |
|---|---|---|---|---|
| 4. Voyant de frein, ABS ou stabilité | `SERVICE BRAKES` | 39 | 15 / 38 | faible |
| 4. Voyant de frein, ABS ou stabilité | `ELECTRICAL SYSTEM` | 21 | 8 / 38 | faible |
| 4. Voyant de frein, ABS ou stabilité | `VEHICLE SPEED CONTROL` | 8 | 3 / 38 | faible |
| 5. Voyant moteur allumé | `ENGINE` | 51 | 49 / 97 | moyenne |
| 5. Voyant moteur allumé | `POWER TRAIN` | 13 | 13 / 97 | moyenne |
| 5. Voyant moteur allumé | `FUEL/PROPULSION SYSTEM` | 9 | 9 / 97 | moyenne |
| 6. Difficulté au démarrage | `ENGINE` | 27 | 6 / 22 | faible |
| 6. Difficulté au démarrage | `ELECTRICAL SYSTEM` | 23 | 5 / 22 | faible |
| 6. Difficulté au démarrage | `POWER TRAIN` | 14 | 3 / 22 | faible |
| 7. Perte de puissance ou calage | `ENGINE` | 33 | 34 / 104 | moyenne |
| 7. Perte de puissance ou calage | `POWER TRAIN` | 15 | 16 / 104 | moyenne |
| 7. Perte de puissance ou calage | `ELECTRICAL SYSTEM` | 12 | 13 / 104 | moyenne |
| 8. Surchauffe ou refroidissement | `ENGINE` | 53 | 20 / 38 | faible |
| 8. Surchauffe ou refroidissement | `ENGINE AND ENGINE COOLING` | 13 | 5 / 38 | faible |
| 8. Surchauffe ou refroidissement | `ELECTRICAL SYSTEM` | 11 | 4 / 38 | faible |
| 9. Batterie ou alternateur | `ELECTRICAL SYSTEM` | 43 | 9 / 21 | faible |
| 9. Batterie ou alternateur | `ENGINE` | 14 | 3 / 21 | faible |
| 10. Éclairage qui clignote | `EXTERIOR LIGHTING` | 39 | 9 / 23 | faible |
| 10. Éclairage qui clignote | `ELECTRICAL SYSTEM` | 17 | 4 / 23 | faible |

**Symptômes sans règle (en attente du fichier complet)** : 1. Bruit au freinage (3 plaintes repérées),
2. Pédale de frein molle (10), 3. Vibrations au freinage (8). Le freinage est presque absent de l'échantillon.

## Algorithme

1. Récupérer les symptômes cochés. Ceux qui n'ont pas de règle sont ignorés.
2. Pour chaque règle d'un symptôme coché, ajouter son **poids** au score de la cause.
3. Calculer le score affiché : `score de la cause ÷ somme des scores × 100`, arrondi à l'entier.
4. Classer les causes par score décroissant. En cas d'égalité : le plus grand nombre de plaintes sous-jacentes
   (somme de la colonne « Plaintes »), puis l'ordre alphabétique.
5. Pour chaque cause classée, chercher les problèmes connus **du véhicule choisi** liés à ce composant.
6. Remplir l'explication : quels symptômes ont apporté combien de points à la cause, et combien de signalements
   existent pour ce véhicule et ce composant.

### Exemple chiffré

L'utilisateur coche « Voyant moteur allumé » (5) et « Surchauffe ou refroidissement » (8).

| Cause | Points du symptôme 5 | Points du symptôme 8 | Score | Score affiché |
|---|---|---|---|---|
| `ENGINE` | 51 | 53 | 104 | **69 %** |
| `POWER TRAIN` | 13 | | 13 | 9 % |
| `ENGINE AND ENGINE COOLING` | | 13 | 13 | 9 % |
| `ELECTRICAL SYSTEM` | | 11 | 11 | 7 % |
| `FUEL/PROPULSION SYSTEM` | 9 | | 9 | 6 % |

Somme des scores : 104 + 13 + 13 + 11 + 9 = 150, donc `ENGINE` = 104 ÷ 150 = 69 %. `POWER TRAIN` et
`ENGINE AND ENGINE COOLING` sont à égalité à 13 : `POWER TRAIN` passe devant car il repose sur plus de plaintes
(13 contre 5).

## Cas limites

- **Aucun symptôme coché, ou seulement des symptômes sans règle** : aucune règle ne s'applique, le résultat est une
  liste vide (réponse `200` avec `"resultats": []`, pas une erreur). 
- **`carburant`, `boite`, `description`** : ignorés par l'heuristique dans cette version.
- **Véhicule** : les poids sont calculés à partir des données de tous les véhicules. Le véhicule sélectionné sert ensuite à rechercher les problèmes qui lui sont associés.
- **Aucun problème connu pour ce véhicule et cette cause** : la cause apparaît dans le classement, mais aucun probleme n'est associé.
- **Égalité de scores** : règle de l'étape 4 de l'algorithme.

## Complexité

Soit s le nombre de symptômes sélectionnés, avec un maximum de 10, k le nombre de règles par symptôme, avec un maximum de 3, et c le nombre de causes différentes obtenues.

- Le calcul des scores est en O(s × k).
- Le classement des causes est en O(c log c).
- Le calcul des scores ne dépend pas directement du nombre de plaintes présentes dans la base, car les poids sont calculés à l'avance.
- La recherche des problèmes associés au véhicule dépend de la base de données. Les index prévus sur probleme_composant et vehicule_probleme permettent de faciliter cette recherche.