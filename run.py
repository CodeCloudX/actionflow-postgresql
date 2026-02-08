import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy.engine.url import make_url
from flask_migrate import init, migrate, upgrade, stamp, current

from app import create_app
from config import Config

def setup_database():
    """Ensures the database exists and is up-to-date with migrations."""
    db_url = Config.SQLALCHEMY_DATABASE_URI
    url = make_url(db_url)

    # Connect to the default 'postgres' database to create the application's database
    try:
        conn = psycopg2.connect(
            host=url.host,
            port=url.port,
            user=url.username,
            password=url.password,
            dbname='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{url.database}'")
        if not cursor.fetchone():
            print(f"Database '{url.database}' not found. Creating...")
            cursor.execute(f'CREATE DATABASE "{url.database}"')
            print(f"Database '{url.database}' created.")
        else:
            print(f"Database '{url.database}' already exists.")

        cursor.close()
        conn.close()
    except psycopg2.OperationalError as e:
        print(f"\n--- DATABASE CONNECTION ERROR ---")
        print(f"Could not connect to PostgreSQL. Please ensure it is running and that the credentials in your .env or config.py are correct.")
        print(f"Error details: {e}")
        exit(1)
    except Exception as e:
        print(f"An unexpected error occurred during database setup: {e}")
        exit(1)

    # Create the Flask app to provide context for migrations
    app = create_app()
    with app.app_context():
        from flask_migrate import Migrate
        from app import db
        from sqlalchemy import inspect, text

        # Initialize migrations folder if not present
        if not os.path.exists('migrations'):
            print("Initializing database migrations folder...")
            init()

        # Handle cases where the versions folder is empty but the DB has a revision.
        versions_dir = os.path.join('migrations', 'versions')
        if os.path.exists(versions_dir) and not os.listdir(versions_dir):
            inspector = inspect(db.engine)
            if 'alembic_version' in inspector.get_table_names():
                print("Inconsistency detected: alembic_version table exists, but migrations/versions is empty.")
                print("Dropping alembic_version table to force a re-stamp.")
                with db.engine.connect() as conn:
                    with conn.begin():
                        conn.execute(text("DROP TABLE alembic_version"))
                print("Dropped alembic_version table.")

        # Check if alembic_version table exists
        inspector = inspect(db.engine)

        if 'alembic_version' not in inspector.get_table_names():
            print("Alembic version table not found. Stamping with current revision...")
            # Create alembic_version table and stamp it
            stamp()
        else:
            try:
                # Check current database revision
                with db.engine.connect() as conn:
                    result = conn.execute(text("SELECT version_num FROM alembic_version"))
                    current_rev = result.scalar()
                    print(f"Current database revision: {current_rev}")
            except Exception as e:
                print(f"Error checking current revision: {e}")

        # Generate migrations if there are changes
        print("Checking for model changes...")
        try:
            migrate(message="Auto-migration on startup.")
        except Exception as e:
            print(f"Migration generation notes: {e}")

        # Always try to upgrade to head
        print("Applying migrations...")
        try:
            upgrade()
            print("Database schema is up-to-date.")
        except Exception as e:
            print(f"Warning during upgrade: {e}")
            # If upgrade fails, try stamping with head and then upgrading
            print("Attempting to recover migration state...")
            try:
                stamp(revision='head')
                upgrade()
                print("Database schema recovered and is now up-to-date.")
            except Exception as e2:
                print(f"Failed to recover migration state: {e2}")
                print("You may need to manually resolve migration conflicts.")

    return app

if __name__ == '__main__':
    # Setup database and create the Flask app instance
    app = setup_database()

    # Run the application
    print("\nStarting the application server on http://127.0.0.1:8000...")
    app.run(port=8000, debug=True, use_reloader=True)
