# Vérification locale et intégration BigQuery

## 1. Tests sans connexion cloud

```bash
npm ci
npm test
python3 -m unittest discover -s tests -p 'test_*.py'
python3 -m py_compile scripts/integration_bigquery.py
```

Les neuf tests Node vérifient le graphe compilé : dépendances vers les assertions, contrôle des sources avant préparation, conservation des tombstones dans le MERGE, chemin full refresh, identité stable, paramétrage et échappement du filtre pays. Les quatre tests Python vérifient les garde-fous du lanceur. Ils ne remplacent pas une exécution SQL BigQuery.

Le workflow GitHub Actions n'utilise pas d'identifiants Google Cloud et ne lance pas les tests d'intégration.

## 2. Préparer l'exécution cloud

Utiliser un projet de test autorisé pour BigQuery, avec création de datasets, création de jobs et écriture dans les nouveaux datasets. Prévoir la facturation des requêtes et du stockage. Toutes les ressources de ce scénario sont en multirégion **EU**.

Installer le Google Cloud CLI (`gcloud` et `bq`), puis configurer l'authentification des deux clients :

```bash
gcloud auth login
gcloud auth application-default login
```

`bq` utilise l'identité du CLI ; Dataform utilise les Application Default Credentials. Vérifier qu'elles correspondent aux identités autorisées dans le projet choisi. Le script génère seulement un fichier temporaire de configuration projet/localisation, sans clé de compte de service.

Inspecter le plan avant l'exécution :

```bash
python3 scripts/integration_bigquery.py --project=mon-projet-gcp
```

La commande suivante **crée et modifie des données de test** et exécute des jobs facturables :

```bash
python3 scripts/integration_bigquery.py --project=mon-projet-gcp --execute
```

Le script choisit un préfixe inédit `df_it_<date>_<aléa>`. Chaque création échoue si un dataset du même nom existe ; aucun dataset existant n'est réutilisé. Les sources sont créées à partir de `fixtures/setup.sql`. Le projet d'origine n'est ni chargé ni lu.

## 3. Contrôles attendus du scénario

| Scénario | Résultat vérifié par le lanceur |
|---|---|
| État initial | Trois clients dans la dimension |
| Mise à jour, date inchangée, arrivée ancienne et suppression | Clients 2 et 4 inactifs, client 11 ajouté malgré sa date ancienne, client 5 absent |
| Nouvelle exécution | État métier identique, sans doublon ; date de traitement exclue de la comparaison |
| Changement de pays avec filtre France | Client 2 retiré |
| Suppression du filtre | Client 2 réintroduit une seule fois avec son nouveau pays |
| Doublon dans la source clients | Échec de l'assertion d'unicité et sortie inchangée |
| Correction de la source | Exécution réussie et clés uniques |
| Doublon dans la cible seulement | Deux lignes avant full refresh ; une seule après reconstruction depuis la source saine |
| Ventes synthétiques | Deux groupes, quatre unités, montant total 55 |
| Doublon de vente source | Échec du contrôle source ; ancien datamart inchangé |
| Correction des ventes | Montant total revenu à 55 |

Les scripts de réparation ne sont adaptés qu'aux fixtures : `SELECT DISTINCT` retire ici un doublon strictement identique, et une vente connue est recréée explicitement. Ce ne sont pas des règles génériques de résolution de conflits métier.

Le lanceur vérifie un échec Dataform attendu ainsi que l'identité des données de sortie avant/après. En cas d'échec inattendu, il s'arrête : consulter les journaux, ne pas interpréter une exécution partielle comme un test réussi.

## 4. Rapports et nettoyage

Les journaux numérotés et `result.json` sont enregistrés dans `artifacts/<préfixe>/`, ignoré par Git. Le rapport indique `passed` uniquement lorsque tous les contrôles sont terminés. Une interruption brutale peut empêcher l'écriture du rapport ; l'absence de rapport réussi ne prouve pas une réussite.

Les datasets restent présents après les tests pour permettre l'inspection, y compris après un échec. Ils continuent à occuper du stockage. Pour les supprimer, reprendre **le préfixe exact du rapport** et vérifier les noms dans la console avant d'exécuter :

```bash
PROJECT_ID="mon-projet-gcp"
TEST_PREFIX="df_it_prefixe_exact_du_rapport"
for suffix in raw stage mart dwh assertions; do
  bq --project_id="$PROJECT_ID" rm -r -d "$PROJECT_ID:${TEST_PREFIX}_${suffix}"
done
```

Ne pas employer le préfixe d'un autre environnement. La commande conserve la confirmation interactive de `bq`.

## Après validation

Mettre à jour `docs/VALIDATION.md` avec la date, les versions et les contrôles réellement passés. Une preuve de cette édition reste une validation nouvelle, distincte des exercices historiques de septembre.
