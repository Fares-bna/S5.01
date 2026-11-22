# Choix du modèle d'embeddings (approche B)

## Quoi

L'approche B transforme le texte de l'utilisateur et celui des plaintes NHTSA en vecteurs, puis cherche les plaintes les plus proches (similarité cosinus). Il faut choisir le modèle qui fait cette transformation.

**Modèle retenu : `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`** (vecteurs de 384 nombres, licence Apache 2.0).

## Contraintes

- **Multilingue** : l'utilisateur écrit en français, les plaintes sont en anglais.
- **Léger** : le modèle tourne sur processeur, dans Docker, et sa consommation est mesurée (temps, CodeCarbon).
- **Licence** compatible avec la licence MIT du projet.

## Comparaison

Script : `benchmark/comparer_modeles.py`. Jeu : `data/evaluation/descriptions_modeles.csv`, 20 descriptions en français (2 par symptôme S1 à S10), chacune avec les catégories NHTSA attendues. Corpus : les 996 plaintes de l'échantillon. Lancé le 22/11/2026 sur un MacBook Air (processeur).

Une plainte est « bonne » si une de ses catégories est attendue. Top-3 : part des descriptions avec une bonne plainte dans les 3 premières. MRR : moyenne de 1/rang de la première bonne plainte.

| Modèle | Dim. | Top-1 | Top-3 | MRR | Encodage des 996 plaintes (s) | Requête (ms) |
|---|---|---|---|---|---|---|
| **paraphrase-multilingual-MiniLM-L12-v2** | 384 | **55 %** | **80 %** | **0,72** | **6,7** | **6,3** |
| multilingual-e5-small | 384 | 20 % | 55 % | 0,41 | 15,3 | 6,8 |
| paraphrase-multilingual-mpnet-base-v2 | 768 | 30 % | 65 % | 0,51 | 19,9 | 18,6 |
| multilingual-e5-base | 768 | 35 % | 55 % | 0,49 | 37,5 | 18,6 |

## Pourquoi ce choix

- C'est le meilleur sur la qualité (top-3 80 %, MRR 0,72) **et** le plus rapide (encodage 2 à 6 fois plus court, requête 3 fois plus courte que les modèles de 768).
- Des vecteurs de 384 nombres prennent deux fois moins de place que ceux de 768 : le calcul de similarité est plus rapide et le stockage plus petit.
- Le choix ne demande donc aucun compromis entre qualité et coût sur nos données.

## Pièges et limites

- **Petit jeu de test** (20 descriptions) : une description en plus ou en moins change le top-3 de 5 points. Les écarts entre MiniLM et les autres (15 à 25 points) restent nets, mais le chiffre est à reconfirmer sur le fichier complet.
- **Catégories larges** : ENGINE couvre beaucoup de plaintes, donc S1, S2, S3 et S8 sont plus faciles à « réussir ». La mesure compare bien les modèles entre eux, elle ne donne pas la précision finale de l'approche B.
- **Modèles E5** : ils demandent les préfixes `query:` et `passage:` (ajoutés par le script). Leurs résultats faibles viennent peut-être de textes de plaintes longs et abîmés ; non creusé, puisque MiniLM gagne déjà.
- **Temps de chargement et RAM** affichés par le script : non retenus. Le premier lancement inclut le téléchargement du modèle, et la mesure de RAM dans un même processus est faussée par les modèles précédents (une valeur négative est sortie).
