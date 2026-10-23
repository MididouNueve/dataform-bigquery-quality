# Modifications de l'édition portfolio

Ces changements ont été préparés le 23 octobre 2026, après les exercices historiques de septembre. Le dossier d'origine est conservé séparément et n'a pas été modifié.

| Point | Exercice récupéré | Édition portfolio |
|---|---|---|
| Projet et datasets | Projet personnel codé en dur | Projet configurable et préfixe de datasets |
| Date de reprise clients | Références à `customer_dim` et `customer_1c`, distinctes de `customers_dim` | Suppression de ces références et du seuil global |
| Lecture clients | Filtre sur la date source avec un seuil susceptible d'être une date de traitement | Relecture complète du snapshot ; dates source et traitement conservées séparément |
| Identité client | Clé incluant le pays | Clé basée sur `customer_id` uniquement |
| Filtre pays | Filtrage avant la mise à jour de la cible | Marquage `is_in_scope`, passage de toutes les lignes au MERGE, puis retrait des lignes hors périmètre |
| Suppression | Condition sur statut et date de reprise | Suppression de tous les tombstones de la cible après le MERGE |
| Clé composite du datamart | Concaténation avec séparateur ambigu | Sérialisation JSON d'une structure avant SHA256 |
| Qualité ventes | Assertions après agrégation | Contrôle supplémentaire des clés source, références et lignes de vente avant préparation |
| Qualité clients | Unicité et champs requis | Date source requise et statut limité à `active`, `inactive`, `to_delete` |
| Données publiées | Fichiers d'atelier dont la provenance personnelle n'est pas établie | Petit jeu synthétique créé pour cette édition |
| Outillage | CLI local 3.0.68 | CLI 3.1.2 verrouillé, tests locaux et workflow CI |

## Conséquences attendues à vérifier dans BigQuery

- Une modification sans actualisation de `technical_date` est désormais reprise : c'est un changement volontaire par rapport à un filtre temporel.
- Un client qui change de pays conserve sa clé. Si le filtre est `France`, un client devenu belge est retiré de la dimension lors du passage de sa ligne source.
- La date `technical_date` de préparation change à chaque exécution. L'idempotence recherchée concerne les valeurs métier et l'unicité, pas les métadonnées de traitement.
- Si une ligne disparaît physiquement de la source, elle reste dans la dimension incrémentale. Le contrat de suppression exige un tombstone ; un full refresh reconstruit la dimension depuis la source disponible.
- Un doublon source provoque un échec d'assertion. Le traitement ne choisit pas arbitrairement une version à conserver.

## Migration

Cette édition doit être démarrée dans de **nouveaux datasets**. Les clés ont changé et le contrat de lecture aussi : ne pas appliquer un simple MERGE sur les tables historiques. Les tests fournis imposent un espace de test neuf. Aucune migration ni modification des ressources historiques n'a été effectuée.

Une extraction réellement incrémentale à grand volume demanderait un autre contrat : journal de changements fiable, identifiants de lots ou dates source monotones, gestion des arrivées tardives et des suppressions, suivi durable du curseur et validation de la reprise après échec.
