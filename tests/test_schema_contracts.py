from schema_generator_core import SchemaContract


def test_schema_table_count(parsed_schema: SchemaContract):
    """The canonical PixelFed contract must define exactly 54 relational tables."""
    assert len(parsed_schema.tables) == 54, f"Expected 54 tables, got {len(parsed_schema.tables)}"


def test_schema_column_count(parsed_schema: SchemaContract):
    """The canonical schema must contain 555 defined column attributes."""
    total_columns = sum(len(table.columns) for table in parsed_schema.tables.values())
    assert total_columns == 555, f"Expected 555 columns across 54 tables, got {total_columns}"


def test_essential_core_tables_exist(parsed_schema: SchemaContract):
    """Ensure core operational and analytics tables are defined."""
    required = {
        "users",
        "profiles",
        "statuses",
        "media",
        "likes",
        "comments",
        "followers",
        "hashtags",
        "status_hashtags",
        "instances",
        "stories",
    }
    missing = required - set(parsed_schema.tables.keys())
    assert not missing, f"Missing critical schema tables: {missing}"


def test_primary_keys_defined(parsed_schema: SchemaContract):
    """Core tables must have defined primary key structures."""
    for table_name in ("users", "profiles", "statuses", "likes", "comments", "media"):
        table = parsed_schema.tables[table_name]
        pk_cols = [c.name for c in table.columns if c.primary_key]
        assert pk_cols, f"Table {table_name} missing primary key definition"


def test_column_names_unique_per_table(parsed_schema: SchemaContract):
    """Each table must have strictly unique column identifiers."""
    for table_name, table in parsed_schema.tables.items():
        col_names = [col.name for col in table.columns]
        assert len(col_names) == len(set(col_names)), f"Duplicate columns detected in {table_name}"
