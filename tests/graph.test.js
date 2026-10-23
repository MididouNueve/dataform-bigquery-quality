const { test } = require('node:test');
const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const cli = path.join(root, 'node_modules', '.bin', 'dataform');

function compile(args = []) {
  const result = spawnSync(cli, ['compile', root, '--json', ...args], { encoding: 'utf8' });
  assert.equal(result.status, 0, result.stderr || result.stdout);
  const graph = JSON.parse(result.stdout);
  assert.deepEqual(graph.graphErrors || {}, {});
  return graph;
}
const graph = compile();
const table = name => graph.tables.find(t => t.target.name === name);
const dependencies = t => t.dependencyTargets.map(d => d.name);

test('both published outputs depend on their quality assertions', () => {
  const clients = dependencies(table('customers_dim'));
  assert.ok(clients.includes('stg_02_customers_assertions_unique_key'));
  assert.ok(clients.includes('stg_02_customers_assertions_not_null'));
  const sales = dependencies(table('mart_weekly_sales'));
  for (const name of ['raw_sales_references_valid', 'stg_01_mart_weekly_sales_assertion_unique_key', 'stg_01_mart_weekly_sales_assertion_not_null']) {
    assert.ok(sales.includes(name));
  }
});

test('source duplicates are gated before sales preparation', () => {
  assert.ok(dependencies(table('stg_01_sales_prepared')).includes('raw_sales_references_valid'));
});

test('source snapshot does not silently omit old timestamps or out-of-scope clients', () => {
  const sql = table('stg_02_customers_prepared').query;
  assert.doesNotMatch(sql, /\bWHERE\b/i);
  assert.doesNotMatch(sql, /incremental_timestamp|customer_1c|customer_dim\b/);
  assert.match(sql, /c\.technical_date AS source_date/);
});

test('country is not part of customer identity', () => {
  const key = table('stg_02_customers_prepared').query.split(' AS key')[0];
  assert.match(key, /customer_id/);
  assert.doesNotMatch(key, /country/);
  assert.deepEqual(table('customers_dim').uniqueKey, ['key']);
});

test('incremental input preserves tombstones; rebuild excludes deleted/out-of-scope rows', () => {
  const t = table('customers_dim');
  assert.doesNotMatch(t.incrementalQuery, /\bWHERE\b/i);
  assert.match(t.query, /status != 'to_delete' AND is_in_scope/);
  assert.match(t.incrementalPostOps.join('\n'), /status = 'to_delete' OR NOT is_in_scope/);
});

test('project and dataset prefix overrides apply to every target and source', () => {
  const g = compile(['--default-database=portfolio-test-project', '--vars=datasetPrefix=df_it_unit,filterCountry=France']);
  for (const action of [...g.tables, ...g.assertions, ...g.declarations]) {
    assert.equal(action.target.database, 'portfolio-test-project');
    assert.ok(action.target.schema.startsWith('df_it_unit_'));
  }
  assert.match(g.tables.find(t => t.target.name === 'stg_02_customers_prepared').query, /c.country = "France"/);
});

test('country with a quote is escaped as a SQL literal', () => {
  const g = compile(['--vars=filterCountry=A"B']);
  assert.ok(g.tables.find(t => t.target.name === 'stg_02_customers_prepared').query.includes('c.country = "A\\"B"'));
});

test('unsafe dataset prefix is rejected at compile time', () => {
  const result = spawnSync(cli, ['compile', root, '--vars=datasetPrefix=bad-prefix'], { encoding: 'utf8' });
  assert.notEqual(result.status, 0);
});

test('each declared dependency resolves to an action in the graph', () => {
  const actions = [...graph.tables, ...graph.assertions, ...graph.declarations];
  const id = t => `${t.database}.${t.schema}.${t.name}`;
  const known = new Set(actions.map(a => id(a.target)));
  for (const a of actions) for (const d of a.dependencyTargets || []) assert.ok(known.has(id(d)), id(d));
});
