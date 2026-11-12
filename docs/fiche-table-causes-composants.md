# Fiche : table causes ↔ composants

Responsable : Fares · Partenaire : Yasmine

## Quoi

Deux fichiers dans `bdd/donnees/` :

- `cause.csv` : les 15 causes de panne que DiagDuo peut proposer (C1 à C15), avec le carburant ou la boîte concernés et un niveau d'urgence.
- `cause_composant.csv` : pour chaque cause, la ou les catégories de composants NHTSA qui lui correspondent (25 liens).

Le script `scripts/lister_composants.py` liste les composants réellement présents dans l'échantillon, avec leur nombre de plaintes. C'est lui qui a servi à choisir les catégories.

## Pourquoi

Les plaintes NHTSA ne contiennent pas de « cause » ni de « symptôme » : chaque plainte est seulement rangée par composant (colonne `COMPDESC`), avec un texte libre en anglais.

Pour que l'approche A (heuristique) puisse dire « la batterie est une cause probable », il faut relier nos causes à ces composants. On peut alors compter les plaintes de chaque cause, ce qui donne les poids de l'heuristique.

Une cause peut toucher plusieurs composants (les freins : `SERVICE BRAKES` et `SERVICE BRAKES, HYDRAULIC`), et un composant plusieurs causes (`ELECTRICAL SYSTEM` : batterie, alternateur, démarreur). C'est une relation plusieurs à plusieurs, d'où une table de liaison à deux colonnes.

## Choix faits

- **On relie les causes aux catégories, pas aux noms complets.** Un nom complet comme `ELECTRICAL SYSTEM:ALTERNATOR/GENERATOR/REGULATOR` a pour catégorie `ELECTRICAL SYSTEM` (partie avant le premier « : », comme dans l'ingestion de Yasmine). L'échantillon compte 67 noms complets, mais seulement 30 catégories, plus stables d'une version du fichier à l'autre.
- **Les variantes avec une virgule restent séparées.** `SERVICE BRAKES` et `SERVICE BRAKES, HYDRAULIC` sont deux catégories différentes : c'est la table qui les relie toutes les deux à la cause C2.
- **Valeurs sans accents ni espaces** pour `carburant`, `boite` et `urgence` (ex. `ne_pas_rouler`), comme pour la gravité dans la base.

## Pièges

- Plusieurs causes partagent la même catégorie (C1, C13 et C14 sont toutes dans `ELECTRICAL SYSTEM`). Le composant seul ne suffit pas à les distinguer : il faudra les mots-clés anglais de chaque cause (voir le document des libellés) pour lire le texte des plaintes.
- Les catégories diesel (`FUEL SYSTEM, DIESEL`) sont très rares dans les données américaines : les causes C7 à C9 reposent surtout sur les règles diesel de l'heuristique.
- Les fichiers ne sont pas encore chargés en base : les tables `cause` et `cause_composant` restent à ajouter au schéma (avec Myriam).
