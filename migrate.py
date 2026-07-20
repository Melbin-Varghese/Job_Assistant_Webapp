"""
migrate.py
One-off migration script for existing databases created before the
per-application resume feature was added. Adds the two new columns
to `applications` (resume_stored_filename, resume_original_filename)
if they aren't already there.

`db.create_all()` only creates tables that don't exist yet -- it never
alters an existing table to add new columns, which is why this script
is needed for databases created before this feature.

Run once, from the project root, with the same Python environment /
.env you use for the app:

    python migrate.py

Safe to run more than once -- it checks for each column before adding
it, so re-running it after it's already been applied is a no-op.
"""

from sqlalchemy import inspect, text

from app import app
from extensions import db

COLUMNS_TO_ADD = [
    ("resume_stored_filename", "VARCHAR(255) NULL"),
    ("resume_original_filename", "VARCHAR(255) NULL"),
]


def column_exists(inspector, table_name, column_name):
    existing_columns = {col["name"] for col in inspector.get_columns(table_name)}
    return column_name in existing_columns


def main():
    with app.app_context():
        inspector = inspect(db.engine)

        if "applications" not in inspector.get_table_names():
            print("No 'applications' table found -- run the app once first "
                  "so db.create_all() can create the base tables, then "
                  "re-run this script.")
            return

        for column_name, column_def in COLUMNS_TO_ADD:
            if column_exists(inspector, "applications", column_name):
                print(f"[skip] applications.{column_name} already exists.")
                continue

            print(f"[add]  applications.{column_name} ...")
            with db.engine.begin() as connection:
                connection.execute(
                    text(f"ALTER TABLE applications ADD COLUMN {column_name} {column_def}")
                )
            print(f"[done] applications.{column_name} added.")

        print("\nMigration complete.")


if __name__ == "__main__":
    main()