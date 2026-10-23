#!/usr/bin/env python3
"""Opt-in cloud integration tests. No BigQuery call without --execute.

Uses fresh, uniquely named datasets and synthetic fixtures. Retains datasets and
logs for inspection on both success and failure; see docs/TESTS.md for cleanup.
"""
import argparse
import datetime
import json
import pathlib
import re
import subprocess
import tempfile
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]


def validate_project(project):
    if not re.fullmatch(r"[a-z][a-z0-9-]{4,28}[a-z0-9]", project):
        raise ValueError("Expected a standard GCP project ID (6–30 characters).")
    if project == "example-gcp-project":
        raise ValueError("Replace the example project ID.")
    return project


def new_prefix():
    return "df_it_" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S") + "_" + uuid.uuid4().hex[:8]


def render(sql, project, prefix):
    validate_project(project)
    if not re.fullmatch(r"df_it_[a-z0-9_]+", prefix):
        raise ValueError("Integration datasets must have a df_it_ prefix.")
    return sql.replace("{{PROJECT}}", project).replace("{{PREFIX}}", prefix)


class Suite:
    def __init__(self, project, prefix, credentials):
        self.project, self.prefix, self.credentials = project, prefix, credentials
        self.output = ROOT / "artifacts" / prefix
        self.output.mkdir(parents=True, exist_ok=False)
        self.checks = []
        self.sequence = 0

    def command(self, args):
        self.sequence += 1
        result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
        (self.output / f"{self.sequence:03d}.log").write_text(result.stdout + "\n" + result.stderr)
        return result

    def sql(self, query, rows=False):
        result = self.command([
            "bq", f"--project_id={self.project}", "--location=EU", "--format=json",
            "query", "--use_legacy_sql=false", "--max_rows=1000",
            render(query, self.project, self.prefix)
        ])
        if result.returncode:
            raise RuntimeError(f"BigQuery failed; see {self.output}/{self.sequence:03d}.log")
        return json.loads(result.stdout) if rows else None

    def expect(self, name, expression):
        self.sql(f"ASSERT ({expression}) AS 'Portfolio integration check';")
        self.checks.append({"check": name, "status": "passed"})

    def run(self, tag, country="France", full=False, expected_assertion=None):
        args = [str(ROOT / "node_modules/.bin/dataform"), "run", str(ROOT),
                f"--credentials={self.credentials}", f"--default-database={self.project}",
                "--default-location=EU", f"--assertion-schema={self.prefix}_assertions",
                f"--vars=datasetPrefix={self.prefix},filterCountry={country}",
                f"--tags={tag}", "--include-deps"]
        if full:
            args.append("--full-refresh")
        result = self.command(args)
        if expected_assertion:
            text = result.stdout + result.stderr
            if result.returncode == 0 or expected_assertion not in text or not re.search(r"fail", text, re.I):
                raise AssertionError(f"Expected {expected_assertion} to fail; inspect {self.output}")
        elif result.returncode:
            raise RuntimeError(f"Dataform failed; inspect {self.output}/{self.sequence:03d}.log")

    def snapshot(self, table, business_only=False):
        value = "(SELECT AS STRUCT t.* EXCEPT(technical_date))" if business_only else "t"
        return self.sql(f"SELECT TO_JSON_STRING({value}) AS row FROM `{{{{PROJECT}}}}.{{{{PREFIX}}}}_{table}` t ORDER BY row", rows=True)

    def unchanged(self, name, before, table, business_only=False):
        if self.snapshot(table, business_only) != before:
            raise AssertionError(name)
        self.checks.append({"check": name, "status": "passed"})

    def execute(self):
        # bq mk fails if a dataset exists: never reuse or overwrite an existing suite.
        for suffix in ("raw", "stage", "mart", "dwh", "assertions"):
            result = self.command(["bq", f"--project_id={self.project}", "--location=EU", "mk", "--dataset", f"{self.project}:{self.prefix}_{suffix}"])
            if result.returncode:
                raise RuntimeError("Dataset creation failed; no existing dataset will be reused.")
        self.sql((ROOT / "fixtures/setup.sql").read_text())
        self.run("dwh", full=True)
        self.expect("initial three clients", "SELECT COUNT(*) = 3 FROM `{{PROJECT}}.{{PREFIX}}_dwh.customers_dim`")
        self.sql("""
          UPDATE `{{PROJECT}}.{{PREFIX}}_raw.customers` SET status='inactive', technical_date=CURRENT_TIMESTAMP() WHERE customer_id=2;
          UPDATE `{{PROJECT}}.{{PREFIX}}_raw.customers` SET status='inactive' WHERE customer_id=4;
          UPDATE `{{PROJECT}}.{{PREFIX}}_raw.customers` SET status='to_delete', technical_date=CURRENT_TIMESTAMP() WHERE customer_id=5;
          INSERT INTO `{{PROJECT}}.{{PREFIX}}_raw.customers`
          SELECT * REPLACE(11 AS customer_id, 'customer-11@example.invalid' AS email,
            'Client11' AS first_name, 'active' AS status, TIMESTAMP '2000-01-01' AS technical_date)
          FROM `{{PROJECT}}.{{PREFIX}}_raw.customers` WHERE customer_id=2;
        """)
        self.run("dwh")
        self.expect("insert, update without source date change, tombstone and late timestamp", """
          SELECT COUNT(*)=3 AND COUNTIF(customer_id=2 AND status='inactive')=1
            AND COUNTIF(customer_id=4 AND status='inactive')=1
            AND COUNTIF(customer_id=11 AND status='active')=1 AND COUNTIF(customer_id=5)=0
          FROM `{{PROJECT}}.{{PREFIX}}_dwh.customers_dim`""")
        before = self.snapshot("dwh.customers_dim", True)
        self.run("dwh")
        self.unchanged("rerun preserves business state", before, "dwh.customers_dim", True)
        self.sql("UPDATE `{{PROJECT}}.{{PREFIX}}_raw.customers` SET country='Belgium' WHERE customer_id=2")
        self.run("dwh")
        self.expect("country change exits France scope", "SELECT COUNTIF(customer_id=2)=0 FROM `{{PROJECT}}.{{PREFIX}}_dwh.customers_dim`")
        self.run("dwh", country="")
        self.expect("unfiltered run restores one client with changed country", "SELECT COUNTIF(customer_id=2)=1 AND COUNTIF(customer_id=2 AND country='Belgium')=1 FROM `{{PROJECT}}.{{PREFIX}}_dwh.customers_dim`")

        before = self.snapshot("dwh.customers_dim")
        self.sql("INSERT INTO `{{PROJECT}}.{{PREFIX}}_raw.customers` SELECT * FROM `{{PROJECT}}.{{PREFIX}}_raw.customers` WHERE customer_id=11")
        self.run("dwh", country="", expected_assertion="stg_02_customers_assertions_unique_key")
        self.unchanged("customer source duplicate blocks output update", before, "dwh.customers_dim")
        self.sql("CREATE OR REPLACE TABLE `{{PROJECT}}.{{PREFIX}}_raw.customers` AS SELECT DISTINCT * FROM `{{PROJECT}}.{{PREFIX}}_raw.customers`")
        self.run("dwh", country="")
        self.expect("source repair restores uniqueness", "SELECT COUNT(*)=COUNT(DISTINCT key) FROM `{{PROJECT}}.{{PREFIX}}_dwh.customers_dim`")
        self.sql("INSERT INTO `{{PROJECT}}.{{PREFIX}}_dwh.customers_dim` SELECT * FROM `{{PROJECT}}.{{PREFIX}}_dwh.customers_dim` WHERE customer_id=11")
        self.expect("target duplicate actually injected", "SELECT COUNTIF(customer_id=11)=2 FROM `{{PROJECT}}.{{PREFIX}}_dwh.customers_dim`")
        self.run("dwh", country="", full=True)
        self.expect("full refresh repairs target-only duplicate with clean source", "SELECT COUNT(*)=3 AND COUNT(*)=COUNT(DISTINCT key) FROM `{{PROJECT}}.{{PREFIX}}_dwh.customers_dim`")

        self.run("datamart")
        self.expect("sales fixture aggregate", "SELECT COUNT(*)=2 AND SUM(total_quantity)=4 AND SUM(total_sales_eur)=55 FROM `{{PROJECT}}.{{PREFIX}}_mart.mart_weekly_sales`")
        before = self.snapshot("mart.mart_weekly_sales")
        self.sql("INSERT INTO `{{PROJECT}}.{{PREFIX}}_raw.sales` SELECT * FROM `{{PROJECT}}.{{PREFIX}}_raw.sales` WHERE sale_id=1")
        self.run("datamart", expected_assertion="raw_sales_references_valid")
        self.unchanged("sale duplicate blocks publication and preserves previous mart", before, "mart.mart_weekly_sales")
        self.sql("DELETE FROM `{{PROJECT}}.{{PREFIX}}_raw.sales` WHERE sale_id=1 AND technical_operation='INSERT'")
        # Restore precisely the synthetic sale removed above (not a generic deduplication rule).
        self.sql("""INSERT INTO `{{PROJECT}}.{{PREFIX}}_raw.sales`
          SELECT 1, 1, TIMESTAMP '2025-01-06 10:00:00+00', 2,
          [STRUCT(1 AS product_id, 2 AS quantity, NUMERIC '10' AS unit_price_eur),
           STRUCT(2 AS product_id, 1 AS quantity, NUMERIC '25' AS unit_price_eur)],
          NUMERIC '45', TIMESTAMP '2025-01-06 10:00:00+00', 'INSERT', 'synthetic_fixture'""")
        self.run("datamart")
        self.expect("sales source repair", "SELECT SUM(total_sales_eur)=55 FROM `{{PROJECT}}.{{PREFIX}}_mart.mart_weekly_sales`")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--execute", action="store_true", help="Create isolated datasets and run billable BigQuery jobs")
    args = parser.parse_args()
    project = validate_project(args.project)
    prefix = new_prefix()
    if not args.execute:
        print(json.dumps({"mode": "plan only; no cloud access", "project": project,
                          "prefix_example": prefix, "location": "EU",
                          "steps": ["create fresh datasets", "load synthetic fixtures", "test customer lifecycle", "test quality gates and recovery"]}, indent=2))
        return
    with tempfile.TemporaryDirectory(prefix="dataform-portfolio-") as tmp:
        credentials = pathlib.Path(tmp) / "credentials.json"
        credentials.write_text(json.dumps({"projectId": project, "location": "EU"}))
        suite = Suite(project, prefix, credentials)
        report = {"project": project, "prefix": prefix, "location": "EU", "status": "running"}
        try:
            suite.execute()
            report["status"] = "passed"
        except Exception as exc:
            report.update(status="failed", error=str(exc))
            raise
        finally:
            report["checks"] = suite.checks
            (suite.output / "result.json").write_text(json.dumps(report, indent=2))
            print(f"Report: {suite.output / 'result.json'}")
            print(f"Datasets retained: {project}.{prefix}_{{raw,stage,mart,dwh,assertions}}")


if __name__ == "__main__":
    main()
