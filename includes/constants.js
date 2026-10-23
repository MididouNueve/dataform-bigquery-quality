const PROJECT_ID = dataform.projectConfig.defaultDatabase;
const vars = dataform.projectConfig.vars || {};
const prefix = vars.datasetPrefix || "df_demo";
if (!/^[a-z][a-z0-9_]{0,40}$/.test(prefix)) {
  throw new Error("datasetPrefix must start with a lowercase letter and contain only a-z, 0-9, _ (max 41 characters).");
}
const SCHEMAS = {
  RAW: `${prefix}_raw`, STAGE: `${prefix}_stage`,
  MART: `${prefix}_mart`, DWH: `${prefix}_dwh`
};

// JSON serialization preserves field boundaries, unlike delimiter concatenation.
function generateUniqueKey(columns) {
  return `TO_HEX(SHA256(TO_JSON_STRING(STRUCT(${columns.map((c, i) => `${c} AS k${i}`).join(", ")}))))`;
}
function sqlString(value) {
  return JSON.stringify(String(value));
}
function countryPredicate(column) {
  return vars.filterCountry ? `${column} = ${sqlString(vars.filterCountry)}` : "TRUE";
}
module.exports = { PROJECT_ID, SCHEMAS, generateUniqueKey, sqlString, countryPredicate };
