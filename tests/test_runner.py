"""Offline safety checks for the optional cloud test runner, not BigQuery SQL tests."""
import importlib.util
import pathlib
import subprocess
import sys
import unittest
from unittest.mock import patch

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / 'scripts/integration_bigquery.py'
spec = importlib.util.spec_from_file_location('integration', SCRIPT)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class RunnerSafety(unittest.TestCase):
    def test_plan_does_not_start_any_subprocess(self):
        with patch.object(sys, 'argv', [str(SCRIPT), '--project', 'portfolio-test-project']), patch.object(subprocess, 'run') as run:
            runner.main()
            run.assert_not_called()

    def test_refuses_unsafe_identifiers(self):
        for project in ['example-gcp-project', 'x` ; DROP SCHEMA x', '../original']:
            with self.assertRaises(ValueError):
                runner.validate_project(project)
        with self.assertRaises(ValueError):
            runner.render('SELECT 1', 'portfolio-test-project', 'raw_data')

    def test_runs_get_distinct_namespaces(self):
        names = {runner.new_prefix() for _ in range(100)}
        self.assertEqual(len(names), 100)
        for prefix in names:
            self.assertTrue(prefix.startswith('df_it_'))

    def test_fixture_renders_without_unresolved_placeholders(self):
        sql = (SCRIPT.parents[1] / 'fixtures/setup.sql').read_text()
        rendered = runner.render(sql, 'portfolio-test-project', 'df_it_example')
        self.assertNotIn('{{', rendered)
        self.assertNotIn('dataform-workshop-507815', rendered)


if __name__ == '__main__':
    unittest.main()
