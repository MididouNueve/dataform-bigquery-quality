# Transformations et contrôles avec Dataform

**Contexte.** Dans un atelier de bootcamp, des ventes brutes doivent être rapprochées des produits et magasins avant agrégation hebdomadaire dans BigQuery. Un second parcours maintient une dimension clients à partir de changements simulés.

**Contribution historique.** J'ai reproduit et exécuté les modèles SQLX, les jointures, les agrégations et les contrôles qualité. Les éléments retrouvés documentent un scénario d'ajout, de changement de statut et de marquage pour suppression, puis une exécution incrémentale réussie. Une capture distincte montre une reconstruction complète avec des assertions clients réussies.

**Améliorations de l'édition portfolio.** La revue a révélé des références incohérentes pour la date de reprise et une clé client dépendant du pays. La copie préparée remplace ce mécanisme par une relecture complète de la source suivie d'un MERGE par identifiant stable. Elle ajoute un contrôle des clés et références des ventes avant agrégation, des paramètres de déploiement et des tests reproductibles sur des données synthétiques.

**Validation et limites.** La compilation et les tests locaux du graphe sont vérifiés. Un scénario BigQuery couvre les changements clients, les doublons et la reprise, mais son exécution sur cette édition reste à réaliser. Les résultats individuels historiques et le scénario de doublon décrit dans le récit initial ne sont pas confirmés par les captures retrouvées.

**Enseignements.** Une tâche SQL réussie ne prouve pas à elle seule un résultat métier. Les assertions doivent être reliées aux sorties qu'elles protègent. La stratégie de reprise doit distinguer la date source de la date de traitement, et une reconstruction de cible ne corrige pas une source contenant des doublons.

**Technologies.** Dataform, BigQuery, SQL/SQLX, JavaScript ; Python pour le scénario d'intégration et GitHub Actions pour les vérifications locales.
