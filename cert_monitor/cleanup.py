import psycopg2
import yaml
import os
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config():
    with open("config.yaml", "r") as file:
        return yaml.safe_load(file)

def cleanup_database():
    # Load configuration
    config = load_config()
    cleanup_days = config.get('cleanup_days', 7)  # Default to 7 days
    cleanup_enabled = config.get('cleanup_enabled', True)  # Default to True

    if not cleanup_enabled:
        logging.info("Cleanup is disabled (cleanup_enabled = False). Exiting.")
        return

    if cleanup_days == -1:
        logging.info("Cleanup is disabled (cleanup_days = -1). Exiting.")
        return

    try:
        conn = psycopg2.connect(
            dbname="certwatch",
            user="certuser",
            password=os.getenv("POSTGRES_PASSWORD"),
            host="cert-db"
        )
        cursor = conn.cursor()

        if not cleanup_enabled:
            logging.info("Cleanup is disabled (cleanup_enabled = False). Exiting.")
            return

        if cleanup_days == 0:
            # Delete all entries
            logging.info("Deleting all entries from certificates and alerts tables.")
            cursor.execute("DELETE FROM certificates;")
            cursor.execute("DELETE FROM alerts;")
        elif cleanup_days > 0:
            # Delete entries older than the specified number of days
            cutoff_date = datetime.now() - timedelta(days=cleanup_days)
            logging.info(f"Deleting entries older than {cleanup_days} days (cutoff date: {cutoff_date}).")
            cursor.execute("DELETE FROM certificates WHERE last_checked < %s;", (cutoff_date,))
            cursor.execute("DELETE FROM alerts WHERE created_at < %s;", (cutoff_date,))

        conn.commit()
        logging.info("Database cleanup completed successfully.")

    except Exception as e:
        logging.error(f"Error during database cleanup: {e}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    cleanup_database()