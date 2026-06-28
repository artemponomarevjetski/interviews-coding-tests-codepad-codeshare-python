Paste Saver


Save
class sync_platform:

    def sync(domain: str, catalog: str, schema: str, table: str, tags: Optional[list] = None, classifications: Optional[Dict[str, str]] = None, isStarburst: bool = False):
        domain_id = None
        table_asset_type_id = None
        schema_asset = None
        starburst_role_name = "enduser_data_access_role"

        # Color Code
        RED = '\033[31m'  # Dark red
        RESET = '\033[0m'   # Reset to default color

        try:
            # Step 1: Retrieve classifications and tags from DLL statement
            # create_delta_table(catalog, schema, table, table_columns, comment, tblproperties)
            # CDP_SS is a prefix for Immuta temp tags, CDP is a prefix for Collibra perm tags
            # Starburst logic
            if isStarburst:
                classifications = classifications
                tags = tags
                derived_tags = [f"CDP_SS.Schema.{catalog}.{schema}.{table}.Starburst", f"CDP.{catalog}.{schema}.{table}.Starburst", "CDP.Status.Candidate", "CDP_SS.Status.Candidate"]
                tags.extend(derived_tags)
            else:
                # Databricks logic
                classifications, tags = get_classifications_and_tags(catalog, schema, table)
                derived_tags = [f"CDP_SS.Schema.{catalog}.{schema}.{table}.Databricks", f"CDP.{catalog}.{schema}.{table}.Databricks", "CDP.Status.Candidate", "CDP_SS.Status.Candidate", "CDP_SS.CSI_Indicator.Contains_CSI", "CDP_SS.Information_Classification.RESTRICTED_FR"]
                tags.extend(derived_tags)
            
            logger.info(f"Classifications: {json.dumps(classifications, indent=4)}")
            logger.info(f"Tags: {tags}")

            # Step 2:
            # Build a full asset path for catalog, schema and table
            # Catalog = Database
            # domain = "CDP Databricks Derived"

            if isStarburst:
                collibra_full_catalog_path = f"{domain}>{catalog}"
                collibra_full_schema_path = f"{domain}>{catalog}>{schema}"
                collibra_new_full_table_path = f"{domain}>{catalog}>{schema}>{table}"
            else:
                collibra_full_catalog_path = f"{catalog}"
                collibra_full_schema_path = f"{catalog}>{schema}"
                collibra_new_full_table_path = f"{catalog}>{schema}>{table}"

            
            logger.info(f"collibra_full_catalog_path: {collibra_full_catalog_path}")
            logger.info(f"collibra_full_schema_path: {collibra_full_schema_path}")
            logger.info(f"collibra_new_full_table_path: {collibra_new_full_table_path}")

            # Create clients dynamically
            collibra_client = CollibraClient(config=collibra_config)
            immuta_client = ImmutaClient(config=immuta_config)
            starburst_client = StarburstClient(config=starburst_config)

            if isStarburst:
                domain_id = None
            else:
                domain_id = collibra_client.get_domain_id(domain)

            logger.info(f"domain_id: {domain_id}")

            data_structure_type_ids = {
                "table": "00000000-0000-0000-0000-000000031007", 
                "view": "00000000-0000-0000-0001-000400000009"
                }
            
            collibra_catalog_asset = collibra_client.get_asset_by_full_path(collibra_full_catalog_path, domain_id)
            logger.info(f"collibra_catalog_asset: {collibra_catalog_asset}")
            logger.info(f"collibra_catalog_asset full name: {collibra_catalog_asset.full_name}")
            logger.info(f"collibra_catalog_asset id: {collibra_catalog_asset.id}")

            collibra_schema_asset = collibra_client.get_asset_by_full_path(collibra_full_schema_path, domain_id)
            logger.info(f"collibra_schema_asset: {collibra_schema_asset}")
            logger.info(f"collibra_schema_asset full name: {collibra_schema_asset.full_name}")
            logger.info(f"collibra_schema_asset id: {collibra_schema_asset.id}")

            collibra_schema_asset_type_id = collibra_schema_asset.type_id
            logger.info(f"collibra_schema_asset_type_id: {collibra_schema_asset_type_id}")

            # Immuta processing
            # Immuta Sync V1 for Starburst
            logger.info(f"immuta host: {immuta_config}")

            if isStarburst:
                immuta_sync_result = immuta_client.trigger_immuta_sync_v_1(immuta_config.starburst_host, schema)
            else:
                # Immuta Sync V2 for Databricks
                immuta_sync_result = immuta_client.trigger_immuta_sync_v_2(immuta_config.host, immuta_config.connection_key, catalog, schema)

            # Check if the sync was successful
            bulk_id = immuta_sync_result.get("bulkId")
            logger.info(f"Immuta Sync process succeeded with Bulk ID: {bulk_id}")
 
            bulk_job_status = immuta_client.get_bulk_operation_status(bulk_id)
            logger.info(f"bulk job status: {bulk_job_status}")

            if not immuta_sync_result.get("success"):
                logger.error(f"Immuta Sync process failed: {immuta_sync_result.get('error')}")
            else:
                # bulk_id = immuta_sync_result.get("bulkId")
                # logger.info(f"Immuta Sync process succeeded with Bulk ID: {bulk_id}")

                # DO NOT TURN OFFF SLEEP
                time.sleep(immuta_config.rest_api_sleep)
                data_source_id = immuta_client.get_data_source_id(catalog, schema, table, "Trino" if isStarburst else "Databricks")
                logger.info(f"✅ data_source_id: {RED}{data_source_id}{RESET}")

                # Check and process tag in Immuta
                logger.info(f"Processing tags for Immuta:")
                all_immuta_tags = immuta_client.list_tags()

                for tag in tags:
                    if tag.lower().startswith("cdp."):
                        continue
                    logger.info(f"Processing tag: {tag}")
                    if tag.lower() not in all_immuta_tags:
                        logger.info(f"Immuta tag '{tag}' doesn't exist. Creating...")
                        immuta_client.create_tag(tag)
                        # immuta_client.add_hierarchy_tags(tag)
                        logger.info(f"Immuta tag '{tag}' was created successfully.")
                    else:
                        logger.info(f"Immuta tag '{tag}' already exists.")
                    
                    immuta_client.add_tag_to_data_source(tag, data_source_id)
                    logger.info(f"Immuta tag: {tag} was added to data source {data_source_id} successfully!")

                logger.info(f"Processing classifications for Immuta:")
                for cf in classifications:
                    # Iterate over key-value pairs and treat each as an item
                    for index, (key, value) in enumerate(classifications.items(), start=1):
                        if not key.lower().startswith("cdp_ss."):
                            continue

                        item = f"{key}:{value}"
                        logger.info(f"Processing classification: {item}")
                        if item.lower() not in all_immuta_tags:
                            logger.info(f"Immuta classification: {item} doesn't exist!")
                            immuta_client.create_tag(item)
                            # immuta_client.add_hierarchy_tags(item)
                            logger.info(f"Immuta classification: {item} was created successfully!")
                        else:
                            logger.info(f"Immuta classification tag: {item} aleady exists.")
                        
                        # Add classification to table in Immuta
                        immuta_client.add_tag_to_data_source(item, data_source_id)
                        logger.info(f"Immuta classification: {item} was applied to data source {data_source_id} successfully!")

                if isStarburst:
                    # get Starburst group role ID
                    starburst_role_id = starburst_client.get_role_id(starburst_role_name)

                    # Grant DML access to the role
                    # is_select_granted = starburst_client.grant_role(starburst_role_id, catalog, schema, table)
                    is_select_granted = starburst_client.grant_select(starburst_role_id, catalog, schema, table)
                    if is_select_granted:
                        logger.info(f"select access was granted successfully to role ID: {starburst_role_id} associated with role {starburst_role_name}")
                    else:
                        logger.info(f"Failed to grant select access to role ID: {starburst_role_id} associated with role {starburst_role_name}")
                    
                    time.sleep(starburst_config.rest_api_sleep)
                    is_insert_granted = starburst_client.grant_insert(starburst_role_id, catalog, schema, table)
                    if is_insert_granted:
                        logger.info(f"insert access was granted successfully to role ID: {starburst_role_id} associated with role {starburst_role_name}")
                    else:
                        logger.info(f"Failed to grant insert access to role ID: {starburst_role_id} associated with role {starburst_role_name}")
                    
                    time.sleep(starburst_config.rest_api_sleep)
                    is_delete_granted = starburst_client.grant_delete(starburst_role_id, catalog, schema, table)
                    if is_delete_granted:
                        logger.info(f"delete access was granted successfully to role ID: {starburst_role_id} associated with role {starburst_role_name}")
                    else:
                        logger.info(f"Failed to grant delete access to role ID: {starburst_role_id} associated with role {starburst_role_name}")
                    
                    time.sleep(starburst_config.rest_api_sleep)
                    is_update_granted = starburst_client.grant_update(starburst_role_id, catalog, schema, table)
                    if is_delete_granted:
                        logger.info(f"update access was granted successfully to role ID: {starburst_role_id} associated with role {starburst_role_name}")
                    else:
                        logger.info(f"Failed to grant update access to role ID: {starburst_role_id} associated with role {starburst_role_name}")

                # Refresh database connection
                # schema id is not schema asset id
                schema_id = (
                    collibra_client.get_asset_id(collibra_schema_asset.full_name)
                    if isStarburst
                    else collibra_client.get_schema_id(schema)
                    )

                time.sleep(collibra_config.rest_api_sleep)
                logger.info(f"✅ schema_id for schema {schema}: {schema_id}")

                schema_connection_id = collibra_client.get_schema_connection_id(schema_id)
                logger.info(f"✅ schema_connection_id: {schema_connection_id}")

                edge_connection_id = collibra_client.get_edge_connection_id (schema_connection_id)
                logger.info(f"✅ edge_connection_id: {edge_connection_id}")

                database_id = collibra_client.get_database_id(edge_connection_id, catalog)
                logger.info(f"✅ database_id: {database_id}")

                if isStarburst:
                    collibra_client.refresh_database_connections(edge_connection_id, True)
                    logger.info(f"Starting to trigger Collibra Sync job for Starburst with collibra catalog asset id: {collibra_catalog_asset.id} and schema connection id: {schema_connection_id}")
                    collibra_client.trigger_collibra_sync(collibra_catalog_asset.id, schema_connection_id, isStarburst, True)
                # else:
                #     catalog_schema_path = f"{catalog}.{schema}"
                #     logger.info(f"Starting to trigger Collibra Sync job for Databricks with database id: {database_id}, schema connection id: {schema_connection_id}, catalog schema path: {catalog_schema_path}, domain id: {domain_id}")
                #     collibra_client.trigger_collibra_sync(database_id, schema_connection_id, isStarburst, True, catalog_schema_path, domain_id)

                # Check if new table is ready.
                collibra_new_table_asset = collibra_client.check_asset_by_full_name(collibra_new_full_table_path, domain_id, wait_for_completion=True)
                logger.info(f"collibra_new_table_asset: {collibra_new_table_asset}")
                logger.info(f"collibra_new_table_asset full name: {collibra_new_table_asset.full_name}")
                logger.info(f"collibra_new_table_asset id: {collibra_new_table_asset.id}")

                all_collibra_tags = collibra_client.list_tags()
                # For debugging only
                # logger.info(f"all_collibra_tags: {json.dumps(all_collibra_tags, indent=4)}")

                logger.info(f"Processing classifications for Collibra:")

                if isStarburst:
                    domain_id = None

                for key, value in classifications.items():
                    if key.lower().startswith("cdp_ss."):
                            continue
                    time.sleep(collibra_config.rest_api_sleep)
                    logger.info(f"upserting classification {key}:{value} for collibra")
                    collibra_client.upsert_classification(
                            domain_id, 
                            collibra_new_full_table_path, 
                            f"{key}:{value}", 
                            data_structure_type_ids["table"]
                            )

                logger.info(f"Processing tags for Collibra:")
                for tag in tags:
                    if tag.lower().startswith("cdp_ss."):
                        continue
                    time.sleep(collibra_config.rest_api_sleep)
                    # we do not need to create tags beforehand in Collibra
                    logger.info(f"Adding tag {tag} for collibra new table {collibra_new_table_asset.id} ...")
                    collibra_client.add_tag_to_asset(collibra_new_table_asset.id, tag)
                    logger.info(f"Adding tag {tag} for collibra new table {collibra_new_table_asset.id} is done successfully")

                immuta_client.link_collibra_asset_to_immuta(data_source_id, collibra_new_table_asset.id)
                immuta_client.refresh_tags()
            
                # Remove temp classifications from Immuta
                for key, value in classifications.items():
                    if not key.lower().startswith("cdp_ss."):
                        continue
                    logger.info(f"Removing classification {cf} from immuta with data source id {data_source_id} ......")
                    immuta_client.remove_temp_tag(f"{key}:{value}", data_source_id, "curated")
                    logger.info(f"Removing classification {key}:{value} from immuta with data source id {data_source_id} is done successfully")

                # Remove temp tags from Immuta
                for tag in tags:
                    if tag.lower().startswith("cdp."):
                        continue
                    time.sleep(collibra_config.rest_api_sleep)
                    logger.info(f"Removing tag {tag} from immuta with data source id {data_source_id} ......")
                    immuta_client.remove_temp_tag(tag, data_source_id, "curated")
                    logger.info(f"Removing tag {tag} from immuta with data source id {data_source_id} is done successfully.")

            logger.info("✅ The orchestration process has been successfully completed!")
        except Exception as e:
            logger.error(f"❌ The orcehstration process failed: {e}")
Saved in: logs/excerpts/ (text) | logs/images/ (images)

Paste Saver


Save
import json
import re
import time
import traceback
from typing import Any, Dict, List, Optional, Set, Tuple

# Manual config, if necessary

def safe_remove_all_widgets():
    try:
        dbutils.widgets.removeAll()
    except Exception:
        pass

def safe_text(name: str, defualt: str):
    try:
        dbutils.widgets.get(name)
    except Exception:
        pass

def safe_dropdown(name: str, default: str, choices: List[str]):
    default = str(default)
    choices = [str(c) for c in choices]
    if default not in choices:
        default = choices[0]
    try:
        dbutils.widgets.get(name)
    except Exception:
        dbutils.widgets.dropdown(name, default, choices)

safe_remove_all_widgets()

DEFAULTS = {
    "domain": "CDP Databricks Derived",
    "catalog": "cdp_derived",
    "schema": "lscc_test",
    "table": "lscc_fory_test189",
    "tags_json": '["Shareble_to_dips", "Non-Licensed", "Status.Candidate"]',
    "classification_json": '{"Information Classification": "RESTRICTED FR", "CSI Indicator": "Contains CSI"}',
    "is_starburst": "false",
    "create_demo_object": "false",
    "demo_object_type": "TABLE",
    "new_owner": "", # ask Kishor or Sri
    "transfer_ownership": "false", # put to true when ready
    "dry_run": "true" # put to false when ready
}

safe_text("domain", DEFAULTS["domain"])
safe_text("catalog", DEFAULTS["catalog"])
safe_text("schema", DEFAULTS["schema"])
safe_text("table", DEFAULTS["table"])
safe_text("tags_json", DEFAULTS["tags_json"])
safe_text("classification_json", DEFAULTS["classification_json"])

safe_dropdown("is_starburst", DEFAULTS["is_starburst"], ["false", "true"])
safe_dropdown("create_demo_object", DEFAULTS["create_demo_object"], ["false", "true"])
safe_dropdown("demo_object_type", DEFAULTS["demo_object_type"], ["TABLE", "VIEW"])
safe_text("new_owner", DEFAULTS["new_owner"])
safe_dropdown("transfer_ownership", DEFAULTS["transfer_ownership"], ["false", "true"])
safe_dropdown("dry_run", DEFAULTS["dry_run"], ["true", "false"])

display({"domain": dbutils.widgets.get("domain")})
Saved in: logs/excerpts/ (text) | logs/images/ (images)

%md
# SRCDP11-774 — Transfer Table/View Owner to Service Principal
**Purpose**: Parameterized Databricks utility notebook to transfer ownership of a Unity Catalog **TABLE** or **VIEW**.
It:
1) Reads parameters via widgets (catalog/schema/object + new owner)
2) Builds a fully-qualified name (**FQN**) and `ALTER TABLE|VIEW ... OWNER TO ...` statement
3) Executes (unless `dry_run=true`)
4) Verifies the new owner via `system.information_schema.tables`

## 1) Widgets

Paste Saver


Save
dbutils.widgets.text("domain", "CDP Databricks Derived")
dbutils.widgets.text("catalog", "cdp_derived")
dbutils.widgets.text("schema", "lscc_test")
dbutils.widgets.text("table", "lscc_fory_test189")

dbutils.widgets.text("tags_json", '["Shareble_to_dips", "Non-Licensed", "Status.Candidate"]')
dbutils.widgets.text("classification_json", '{"Information Classification": "RESTRICTED FR", "CSI Indicator": "Contains CSI"}')

dbutils.widgets.text("catalog", DEFAULTS["catalog"])
dbutils.widgets.text("schema", DEFAULTS["schema"])
dbutils.widgets.text("object_name", DEFAULTS["object_name"])
dbutils.widgets.dropdown("object_kind", DEFAULTS["object_kind"], ["TABLE", "VIEW"])
dbutils.widgets.text("new_owner", DEFAULTS["new_owner"])
dbutils.widgets.dropdown("dry_run", DEFAULTS["dry_run"], ["true", "false"])

catalog = dbutils.widgets.get("catalog").strip()
schema = dbutils.widgets.get("schema").strip()
domain = dbutils.widgets.get("domain").strip()
table = dbutils.widgets.get("table").strip()

missing = [k for k, v in {
    "catalog": catalog,
    "schema": schema, 
    "domain": domain,
    "table": table
}.items() if not v]

if missing:
    raise ValueError(f"Missing required fields: {', '.join(missing)}")
Saved in: logs/excerpts/ (text) | logs/images/ (images)


Paste Saver


Save
%md
## 2) Helpers
from typing import Optional

def _w(name: str) -> str:
    return (dbutils.widgets.get(name) or "").strip()

def _is_true(s: str) -> bool:
    return (s or "").strip().lower() in {"1", "true", "t", "yes", "y"}

def quote_ident(identifier: str) -> str:
    """Backtick-quote a Unity Catalog identifier component."""
    if identifier is None:
        identifier = ""
    identifier = identifier.strip()
    if not identifier:
        raise ValueError("Empty identifier")
    # Escape embedded backticks by doubling them.
    identifier = identifier.replace("`", "``")
    return f"`{identifier}`"

def build_fqn_sql(catalog: str, schema: str, name: str) -> str:
    """Return a SQL-safe fully qualified name: `catalog`.`schema`.`name`."""
    return f"{quote_ident(catalog)}.{quote_ident(schema)}.{quote_ident(name)}"

def build_alter_owner_sql(object_kind: str, fqn_sql: str, new_owner: str) -> str:
    object_kind = (object_kind or "").strip().upper()
    if object_kind not in {"TABLE", "VIEW"}:
        raise ValueError("object_kind must be TABLE or VIEW")

    return f"ALTER {object_kind} {fqn_sql} OWNER TO {quote_ident(new_owner)}"

def get_current_owner(catalog: str, schema: str, name: str) -> Optional[str]:
    """Return current owner from UC information schema (works for tables and views)."""
    df = spark.sql(
        f"""
        SELECT table_owner
        FROM system.information_schema.tables
        WHERE table_catalog = '{catalog}'
          AND table_schema  = '{schema}'
          AND table_name    = '{name}'
        """
    )
    rows = df.collect()
    if not rows:
        return None
    return rows[0]["table_owner"]
Saved in: logs/excerpts/ (text) | logs/images/ (images)


Paste Saver


Save
%md
## 3) Read + Validate Inputs
CATALOG = _w("catalog")
SCHEMA = _w("schema")
OBJECT_NAME = _w("object_name")
OBJECT_KIND = _w("object_kind")
NEW_OWNER = _w("new_owner")
DRY_RUN = _is_true(_w("dry_run"))

missing = [k for k, v in {
    "schema": SCHEMA,
    "object_name": OBJECT_NAME,
    "new_owner": NEW_OWNER,
}.items() if not v]

if missing:
    raise ValueError(
        "Missing required widget(s): " + ", ".join(missing) + ". "
        "Fill them at the top of the notebook / in the Job parameters and rerun."
    )

FQN_SQL = build_fqn_sql(CATALOG, SCHEMA, OBJECT_NAME)
ALTER_SQL = build_alter_owner_sql(OBJECT_KIND, FQN_SQL, NEW_OWNER)

print("=== SRCDP11-774 Parameters ===")
print(f"catalog      = {CATALOG}")
print(f"schema       = {SCHEMA}")
print(f"object_name  = {OBJECT_NAME}")
print(f"object_kind  = {OBJECT_KIND}")
print(f"new_owner    = {NEW_OWNER}" )
print(f"dry_run      = {DRY_RUN}")
print(f"FQN (SQL)    = {FQN_SQL}")
print(f"ALTER SQL    = {ALTER_SQL}")
Saved in: logs/excerpts/ (text) | logs/images/ (images)


Paste Saver


Save
%md
## 4) Execute or dry run with no impact on ownership to verify
current_owner_before = get_current_owner(CATALOG, SCHEMA, OBJECT_NAME)
print(f"Current owner (before): {current_owner_before}")

if DRY_RUN:
    print("\nDRY RUN ONLY — not executing ALTER statement.")
else:
    print("\nExecuting ownership transfer...")
    spark.sql(ALTER_SQL)

current_owner_after = get_current_owner(CATALOG, SCHEMA, OBJECT_NAME)
print(f"Current owner (after):  {current_owner_after}")

if not DRY_RUN:
    if current_owner_after != NEW_OWNER:
        raise RuntimeError(
            f"Ownership verification failed. Expected '{NEW_OWNER}', got '{current_owner_after}'."
        )
    print("✅ Ownership transfer verified.")
Saved in: logs/excerpts/ (text) | logs/images/ (images)

Paste Saver


Save
import json
import re
import time
import traceback
from typing import Any, Dict, List, Optional, Set, Tuple

def _ensure_text_widget(name: str, default: str, label: str) -> None:
    try:
        dbutils.widgets.get(name)
    except Exception:
        dbutils.widgets.text(name, default, label)

def _ensure_dropdown_widget(name: str, default: str, choices: List[str], label: str) -> None:
    try:
        dbutils.widgets.get(name)
        return
    except Exception:
        pass

    # Databricks can throw if default not in choices
    if default not in choices:
        choices = [default] + [c for c in choices if c != default]

    try:
        dbutils.widgets.dropdown(name, default, choices, label)
    except Exception:
        # Fallback to text if dropdown isn't supported in this context
        dbutils.widgets.text(name, default, label)

# Required
_ensure_text_widget("domain", "", "domain (required)")
_ensure_text_widget("catalog", "", "catalog (required)")
_ensure_text_widget("schema", "", "schema (required)")
_ensure_text_widget("table", "", "table/view name (required)")

# tags_csv or tags_json -- double-check
_ensure_text_widget("tags_csv", "", "tags_csv (optional; comma/newline-separated)")
_ensure_text_widget("classifications_json", "", "classifications_json (optional; JSON object)")
_ensure_dropdown_widget("is_starburst", "false", ["false", "true"], "is_starburst (optional)")
_ensure_dropdown_widget("dry_run", "false", ["false", "true"], "dry_run (optional)")

def _as_bool(s: str) -> bool:
    return str(s).strip().lower() in {"1", "true", "t", "yes", "y"}

def _parse_tags(tags_csv: str) -> Set[str]:
    if not tags_csv or not tags_csv.strip():
        return set()
    # split by comma OR newline
    raw = re.split(r"[\n,]+", tags_csv)
    return {t.strip() for t in raw if t and t.strip()}

def _parse_classifications(classifications_json: str) -> Dict[str, Any]:
    if not classifications_json or not classifications_json.strip():
        return {}
    try:
        parsed = json.loads(classifications_json)
    except Exception as e:
        raise ValueError(f"Got error: {e}")
    if not isinstance(parsed, dict):
        raise ValueError("classifications_json must decode to a JSON object/dict.")
    return parsed

domain = dbutils.widgets.get("domain").strip()
catalog = dbutils.widgets.get("catalog").strip()
schema = dbutils.widgets.get("schema").strip()
object_name = dbutils.widgets.get("table").strip()

tags_csv = dbutils.widgets.get("tags_csv")
classifications_json = dbutils.widgets.get("classifications_json")
is_starburst = _as_bool(dbutils.widgets.get("is_starburst"))
dry_run = _as_bool(dbutils.widgets.get("dry_run"))

tags = _parse_tags(tags_csv)
classifications = _parse_classifications(classifications_json)

required_missing = [k for k, v in {
    "domain": domain,
    "catalog": catalog,
    "schema": schema,
    "table": table
}.items() if not v]

if required_missing:
    raise ValueError(f"Missing required parameters: {', '.join(required_missing)}")

print("=== SRCDP11-773 parameters ===")
print(json.dumps({
    "domain": domain,
    "catalog": catalog,
    "schema": schema,
    "object_name": object_name,
    "tags_count": len(tags),
    "classifications_keys": list(classifications.keys()),
    "is_starburst": is_starburst,
    "dry_run": dry_run
}, indent=2))

import types

def _try_call_patterns(sync_fn, domain: str, catalog: str, schema: str, obj: str,
                    tags: Set[str], classifications: Dict[str, Any], is_starburst: bool):
    """Try multiple call signatures to be robust against minor API differences."""
    # to study what the API sends to the user
    patterns = [
        ("domain,catalog,schema,obj,tags,cls,isStarburst=..",
        lambda: sync_fn(domain, catalog, schema, obj, tags, classifications, isStarburst=is_starburst)),
        ("domain,catalog,schema,obj,tags,cls,is_starburst=..",
        lambda: sync_fn(domain, catalog, schema, obj, tags, classifications, is_starburst=is_starburst)),
        ("domain,catalog,schema,obj,tags,cls",
        lambda: sync_fn(domain, catalog, schema, obj, tags, classifications)),
        ("domain,catalog,schema,obj,isStarburst=..",
        lambda: sync_fn(domain, catalog, schema, obj, isStarburst=is_starburst)),
        ("domain,catalog,schema,obj,is_starburst=..",
        lambda: sync_fn(domain, catalog, schema, obj, is_starburst=is_starburst)),
        ("domain,catalog,schema,obj",
        lambda: sync_fn(domain, catalog, schema, obj)),
    ]

    last_err = None
    for label, fn in patterns:
        try:
            res = fn()
            print(f"✅ sync_platform.sync succeeded using pattern: {label}")
            return res
        except TypeError as e:
            last_err = e
            # keep trying
        except Exception:
            # non-TypeError likely means the call signature was accepted but the function failed internally;
            # re-raise to surface the true issue.
            raise

    raise TypeError(f"Unable to call sync_platform.sync with any known signature. Last TypeError: {last_err}")

if dry_run:
    print("DRY RUN: skipping sync_platform.sync execution.")
    dbutils.notebook.exit(json.dumps({
        "status": "DRY_RUN",
        "domain": domain,
        "catalog": catalog,
        "schema": schema,
        "object_name": object_name,
        "tags": sorted(list(tags)),
        "classifications": classifications,
        "is_starburst": is_starburst
    }))

if "sync_platform" not in globals():
    raise NameError(
        "sync_platform was not found after importing data_governance_library. "
        "Verify that the library notebook defines `sync_platform`."
    )

if not hasattr(sync_platform, "sync"):
    raise AttributeError(
        "sync_platform.sync was not found. Verify that the library notebook defines a `sync` method."
    )

start_ts = time.time() # future latency optimization
try:
    result = _try_call_patterns(sync_platform.sync, domain, catalog, schema, object_name, tags, classifications, is_starburst)
    elapsed_s = round(time.time() - start_ts, 3)

    print(f"✅ Completed orchestration call in {elapsed_s}s")
    dbutils.notebook.exit(json.dumps({
        "status": "SUCCESS",
        "elapsed_s": elapsed_s,
        "domain": domain,
        "catalog": catalog,
        "schema": schema,
        "object_name": object_name,
        "is_starburst": is_starburst,
        "result_repr": None if result is None else str(result)[:5000]
    }))
except Exception as e:
    elapsed_s = round(time.time() - start_ts, 3)
    err = {
        "status": "FAILED",
        "elapsed_s": elapsed_s,
        "domain": domain,
        "catalog": catalog,
        "schema": schema,
        "object_name": object_name,
        "is_starburst": is_starburst,
        "error_type": type(e).__name__,
        "error_message": str(e),
        "traceback": traceback.format_exc()[:15000],
    }
    print("❌ Orchestration call failed")
    print(json.dumps(err, indent=2))
    raise
Saved in: logs/excerpts/ (text) | logs/images/ (images)

