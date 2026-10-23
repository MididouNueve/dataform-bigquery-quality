# Provenance et preuves

## Attribution

Les modèles SQLX de départ proviennent d'un atelier de bootcamp reproduit et exécuté par Mehdi Zobiri. Ce dépôt présente cette réalisation pédagogique et les modifications de l'édition portfolio ; il ne présente pas l'ensemble du modèle initial comme une conception originale.

La revue, les corrections, les tests et la documentation de cette édition ont été préparés avec l'assistance de Codex. Le nom du bootcamp et la référence du support n'ont pas été fournis dans les éléments récupérés. Aucune licence permissive n'est ajoutée au code dérivé en l'absence d'une licence du support identifiée.

Le parcours introductif `hello_world` est exclu pour concentrer ce dépôt sur les transformations et la qualité. Les données d'origine, identifiants d'accès, captures contenant des informations de compte et dépendances installées ne sont pas inclus dans le paquet publiable.

## Éléments historiques observés

Les captures de l'historique BigQuery ont été fournies par l'auteur. Les heures ci-dessous sont celles affichées le 18 septembre 2026, en UTC+2. Il s'agit d'une lecture de ces captures, pas d'une réexécution des anciens jobs.

| Heure | Élément visible | Portée de la preuve |
|---|---|---|
| 16:07:50 | Modification des clients 2 et 4, marquage `to_delete` du client 5, insertion du client 11 | Script de simulation et job marqué réussi ; pas de compte de lignes affectées |
| 16:08:32 | MERGE de la préparation vers `customers_dim`, suivi d'un DELETE conditionnel | Exécution incrémentale historique marquée réussie ; résultats individuels non visibles |
| 16:12:16 | Modification manuelle de dates techniques dans la source et la dimension | Manipulation de dates documentée |
| 16:20:45 | Retour du client 2 à `active` et actualisation de sa date | UPDATE documenté ; aucun INSERT malgré le commentaire de la requête |

Une autre capture du terminal montre une commande de reconstruction complète avec filtre France, la compilation réussie, les deux assertions clients réussies et la création de la dimension.

Le SQL historique contient la référence `customer_1c` aussi présente dans les fichiers récupérés. Son existence historique comme table externe n'a pas été établie.

## Ce qui n'est pas démontré par les captures

- Les valeurs avant/après de chaque client.
- L'introduction d'un doublon volontaire, l'échec d'assertion associé et le blocage de la sortie.
- La disparition de ce doublon après reconstruction.
- Le résultat métier chiffré du datamart.

L'auteur rapporte avoir réalisé ces exercices ; le dépôt distingue ce récit des éléments vérifiables retrouvés. Les nouveaux scénarios automatisés ne doivent pas être présentés comme des preuves historiques.

## Inspection des fichiers de données d'origine

L'inspection locale a trouvé 10 clients, 6 produits, 3 magasins et deux versions de ventes de 15 et 20 lignes. Les identifiants métier sont uniques dans chaque fichier. La seconde version modifie les ventes 1 et 2 et ajoute les ventes 16 à 20. Un chargement en ajout aurait pu introduire des doublons dans BigQuery, mais ce mode de chargement n'a pas été établi.

Ces fichiers ne sont pas distribués. `fixtures/setup.sql` contient uniquement de nouvelles données de démonstration avec des adresses `example.invalid`.
