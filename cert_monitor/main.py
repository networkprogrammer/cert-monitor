import yaml
from scanner import check_certificates
from db import init_db
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config():
    with open("config.yaml", "r") as file:
        return yaml.safe_load(file)

def main():
    logging.info("Starting certificate monitoring scanner...")

    # Load configuration
    config = load_config()
    domains = config.get('domains', [])
    alert_threshold = config.get('expire_threshold_days', 30)

    # Initialize database
    logging.info("Initializing database...")
    init_db()

    # Scan certificates
    for domain in domains:
        domain_name = domain['name']
        try:
            logging.info(f"Scanning domain: {domain_name}")
            check_certificates(domain_name, alert_threshold)
        except Exception as e:
            logging.error(f"Error scanning domain {domain_name}: {e}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"Critical failure: {e}")