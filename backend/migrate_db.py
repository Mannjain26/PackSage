"""
Database Migration Script for SQLite & PostgreSQL
Adds newly introduced columns to materials and scenarios tables safely.
"""
import sys, os
import sqlite3
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.core.config import settings

def run_migration():
    db_url = settings.DATABASE_URL
    if "sqlite" in db_url:
        db_path = db_url.replace("sqlite:///", "")
        if not os.path.isabs(db_path):
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_path)
        
        print(f"Migrating SQLite DB at: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check existing columns in materials
        cursor.execute("PRAGMA table_info(materials)")
        mat_cols = [row[1] for row in cursor.fetchall()]

        new_mat_cols = [
            ("price_per_kg", "REAL"),
            ("price_per_sqm", "REAL"),
            ("currency", "TEXT DEFAULT 'INR'"),
            ("price_source", "TEXT DEFAULT 'Converter Index'"),
            ("price_last_updated", "TIMESTAMP"),
            ("price_confidence", "TEXT DEFAULT 'Illustrative Demo'"),
            ("material_density_g_cm3", "REAL DEFAULT 0.92"),
            ("wastage_pct_default", "REAL DEFAULT 5.0"),
            ("conversion_cost_default", "REAL DEFAULT 0.25"),
            ("sealing_cost_default", "REAL DEFAULT 0.10"),
            ("moq_kg", "REAL DEFAULT 50.0"),
            ("quantity_discount_pct", "REAL DEFAULT 5.0"),
        ]

        for col_name, col_type in new_mat_cols:
            if col_name not in mat_cols:
                print(f"Adding column {col_name} to materials table")
                cursor.execute(f"ALTER TABLE materials ADD COLUMN {col_name} {col_type}")

        # Check existing columns in scenarios
        cursor.execute("PRAGMA table_info(scenarios)")
        scen_cols = [row[1] for row in cursor.fetchall()]

        new_scen_cols = [
            ("cost_priority", "TEXT DEFAULT 'balanced'"),
            ("package_format", "TEXT DEFAULT 'pouch'"),
            ("product_weight_g", "REAL DEFAULT 100.0"),
            ("package_quantity", "INTEGER DEFAULT 5000"),
            ("currency", "TEXT DEFAULT 'INR'"),
            ("target_cost_per_package", "REAL"),
            ("target_total_budget", "REAL"),
            ("package_length_cm", "REAL"),
            ("package_width_cm", "REAL"),
            ("package_height_cm", "REAL"),
            ("film_area_cm2", "REAL"),
            ("custom_thickness_um", "REAL"),
            ("layer_count", "INTEGER DEFAULT 1"),
            ("closure_cost_per_pkg", "REAL"),
            ("label_cost_per_pkg", "REAL"),
            ("printing_cost_per_pkg", "REAL"),
            ("secondary_pack_cost_per_pkg", "REAL"),
            ("labor_packing_cost_per_pkg", "REAL"),
            ("transport_cost_per_pkg", "REAL"),
            ("wastage_pct_override", "REAL"),
        ]

        for col_name, col_type in new_scen_cols:
            if col_name not in scen_cols:
                print(f"Adding column {col_name} to scenarios table")
                cursor.execute(f"ALTER TABLE scenarios ADD COLUMN {col_name} {col_type}")

        conn.commit()
        conn.close()
        print("SQLite migration completed successfully.")
    else:
        print("Non-sqlite DB detected, Base.metadata.create_all handles table structure.")

if __name__ == "__main__":
    run_migration()
