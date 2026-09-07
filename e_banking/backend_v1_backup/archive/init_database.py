from pathlib import Path
from urllib.parse import urlparse
import os
import sys

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = ROOT.parent / "database" / "SUPABASE_NEW_DATABASE_SETUP.sql"


def get_project_ref(supabase_url: str) -> str:
    host = urlparse(supabase_url).hostname or ""
    if not host.endswith(".supabase.co"):
        raise ValueError("SUPABASE_URL must look like https://<project-ref>.supabase.co")
    return host.split(".")[0]


def main() -> int:
    load_dotenv(ROOT / ".env.backend")

    supabase_url = os.environ.get("SUPABASE_URL", "").strip()
    db_password = os.environ.get("SUPABASE_DB_PASSWORD", "").strip()

    if not supabase_url or not db_password:
        print("Missing SUPABASE_URL or SUPABASE_DB_PASSWORD in .env.backend.")
        print(f"Run the SQL manually in Supabase SQL Editor: {SCHEMA_PATH}")
        return 1

    try:
        import psycopg2
    except ImportError:
        print("Missing psycopg2. Run: python -m pip install -r requirements.txt")
        return 1

    project_ref = get_project_ref(supabase_url)
    db_host = os.environ.get("SUPABASE_DB_HOST", f"db.{project_ref}.supabase.co").strip()
    db_port = int(os.environ.get("SUPABASE_DB_PORT", "5432"))
    db_user = os.environ.get("SUPABASE_DB_USER", "postgres").strip()
    sql = SCHEMA_PATH.read_text(encoding="utf-8")

    print(f"Applying schema to Supabase project: {project_ref}")
    try:
        with psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname="postgres",
            user=db_user,
            password=db_password,
            sslmode="require",
            connect_timeout=20,
        ) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(sql)
    except Exception as exc:
        print(f"Could not apply schema automatically: {exc}")
        print(f"Run the SQL manually in Supabase SQL Editor: {SCHEMA_PATH}")
        print("If using Supabase's pooler, set SUPABASE_DB_HOST, SUPABASE_DB_PORT, and SUPABASE_DB_USER.")
        return 1

    print("Database schema is ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
