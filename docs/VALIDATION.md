# Validation du 23 octobre 2026

## Résultats obtenus localement

| Vérification | Résultat |
|---|---|
| Installation à partir de `package-lock.json` avec `npm ci --ignore-scripts` | Réussie |
| Tests Node sur le graphe et les paramètres | **9/9 réussis** |
| Tests Python du lanceur d'intégration | **4/4 réussis** |
| Vérification syntaxique Python du lanceur | Réussie |
| Compilation Dataform par défaut | **8 modèles, 5 assertions**, sans erreur |
| Compilation avec projet/préfixe différents et filtre France | Réussie dans les tests |
| Audit npm à l'installation | **0 vulnérabilité signalée** dans les dépendances verrouillées à cette date |

Environnement local : macOS, Node.js **26.8.1**, npm **11.19.0**, Dataform CLI **3.1.2**, Dataform Core **3.0.0**.

## Validation sur GitHub

Le workflow **Offline validation** a réussi sur GitHub avec **Node.js 22** le 23 octobre 2026 : installation avec `npm ci`, 9 tests Node, 4 tests Python et vérification syntaxique Python. [Consulter l'exécution sur le commit publié](https://github.com/MididouNueve/dataform-bigquery-quality/actions/runs/39969164194).

Ces tests automatiques ne se connectent pas à BigQuery.

Le CLI 3.0.68 initialement repris avait des dépendances signalées par l'audit npm. La mise à jour du CLI vers 3.1.2 les a résolues sans imposer d'override des dépendances transitives ; les tests ont été relancés sur cette version. Un audit sans alerte n'est pas une garantie d'absence de vulnérabilité.

## Ce qui reste à exécuter

**Le scénario d'intégration BigQuery n'a pas été lancé.** Aucun succès métier de cette édition corrigée n'est donc annoncé. La compilation ne valide pas à elle seule les permissions, les schémas réels, l'exécution du SQL, les volumes modifiés ni le comportement d'une reprise cloud.

La suite opt-in est disponible dans `scripts/integration_bigquery.py`, avec données synthétiques et résultats attendus dans [TESTS.md](TESTS.md). Le mode plan a été vérifié sans appel à un processus externe.

## Distinction historique

L'historique de septembre documente une exécution du modèle original et des manipulations source. Il ne valide pas les modifications d'octobre. Les limites de preuve sont détaillées dans [PROVENANCE.md](PROVENANCE.md).
