from __future__ import annotations

from pathlib import Path

from raw_quality import inject_raw_quality_issues
from schema_generator_core import SchemaDrivenGenerator, parse_as_of


def test_raw_quality_profile_preserves_row_counts_and_relationship_keys(parsed_schema, tmp_path: Path):
    generator = SchemaDrivenGenerator(
        schema=parsed_schema,
        output_dir=tmp_path / "raw",
        seed=81,
        scale=0.03,
        as_of=parse_as_of("2026-10-27T12:00:00Z"),
        formats=set(),
    )
    generator.generate()

    row_counts_before = {name: len(rows) for name, rows in generator.datasets.items()}
    primary_keys_before = {
        table_name: {
            column.name: [row.get(column.name) for row in generator.datasets[table_name]]
            for column in table.columns
            if column.primary_key
        }
        for table_name, table in generator.schema.tables.items()
    }
    foreign_keys_before = {
        (table_name, column_name): [row.get(column_name) for row in generator.datasets[table_name]]
        for table_name, column_name in generator.references
    }

    report = inject_raw_quality_issues(generator, rate=0.025)

    assert report["enabled"] is True
    assert report["synthetic_only"] is True
    assert report["total_injected_issues"] > 0
    assert report["row_count_changed"] is False
    assert report["primary_keys_changed"] is False
    assert report["foreign_keys_changed"] is False
    assert {name: len(rows) for name, rows in generator.datasets.items()} == row_counts_before
    for table_name, columns in primary_keys_before.items():
        for column_name, values in columns.items():
            assert [row.get(column_name) for row in generator.datasets[table_name]] == values
    for (table_name, column_name), values in foreign_keys_before.items():
        assert [row.get(column_name) for row in generator.datasets[table_name]] == values
