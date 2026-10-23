-- Entirely synthetic fixtures for the portfolio edition, created October 2026.
-- Rendered only by scripts/integration_bigquery.py in newly created datasets.
CREATE TABLE `{{PROJECT}}.{{PREFIX}}_raw.customers` AS
SELECT
  id AS customer_id,
  CONCAT('customer-', CAST(id AS STRING), '@example.invalid') AS email,
  CONCAT('Client', CAST(id AS STRING)) AS first_name,
  'Demo' AS last_name,
  DATE '1990-01-01' AS birth_date,
  'France' AS country,
  'Paris' AS city,
  TIMESTAMP '2025-01-01 00:00:00+00' AS registration_date,
  TIMESTAMP '2025-01-01 00:00:00+00' AS updated_at,
  'active' AS status,
  TIMESTAMP '2025-01-01 00:00:00+00' AS technical_date,
  'INSERT' AS technical_operation,
  'synthetic_fixture' AS technical_flow_identifier
FROM UNNEST([2, 4, 5]) id;

CREATE TABLE `{{PROJECT}}.{{PREFIX}}_raw.products` AS
SELECT 1 AS product_id, 'Produit A' AS product_name, 'Demo' AS collection,
  'demo' AS category, NUMERIC '10' AS price_eur
UNION ALL SELECT 2, 'Produit B', 'Demo', 'demo', NUMERIC '25';

CREATE TABLE `{{PROJECT}}.{{PREFIX}}_raw.stores` AS
SELECT 1 AS store_id, 'Magasin Demo' AS store_name, 'Paris' AS city,
  'Ile-de-France' AS region, 'France' AS country;

CREATE TABLE `{{PROJECT}}.{{PREFIX}}_raw.sales` AS
SELECT 1 AS sale_id, 1 AS store_id, TIMESTAMP '2025-01-06 10:00:00+00' AS sale_timestamp,
  2 AS customer_id,
  [STRUCT(1 AS product_id, 2 AS quantity, NUMERIC '10' AS unit_price_eur),
   STRUCT(2 AS product_id, 1 AS quantity, NUMERIC '25' AS unit_price_eur)] AS items,
  NUMERIC '45' AS total_amount_eur,
  TIMESTAMP '2025-01-06 10:00:00+00' AS technical_date,
  'INSERT' AS technical_operation, 'synthetic_fixture' AS technical_flow_identifier
UNION ALL
SELECT 2, 1, TIMESTAMP '2025-01-06 11:00:00+00', 4,
  [STRUCT(1 AS product_id, 1 AS quantity, NUMERIC '10' AS unit_price_eur)],
  NUMERIC '10', TIMESTAMP '2025-01-06 11:00:00+00', 'INSERT', 'synthetic_fixture';
