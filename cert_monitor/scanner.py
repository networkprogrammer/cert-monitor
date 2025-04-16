import ssl
import socket
from cryptography import x509
from cryptography.hazmat.backends import default_backend
import psycopg2
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from datetime import datetime, timezone
import smtplib
from email.mime.text import MIMEText
import yaml
import logging
from OpenSSL import SSL
import os

# Configure logging with timestamps
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def send_alert(subject, body):
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)

    email_config = config['alert_channels']['email']
    if email_config.get('send_email', False):
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = email_config['from']
        msg['To'] = email_config['to']

        with smtplib.SMTP(email_config['smtp_host'], email_config['smtp_port']) as server:
            # server.set_debuglevel(1)  # Enable SMTP debugging
            server.starttls()
            server.sendmail(email_config['from'], email_config['to'], msg.as_string())
    else:
        logging.info(f"LOG: {subject} - {body}")

def get_cert_chain(domain, port=443):
    try:
        ctx = SSL.Context(SSL.TLS_CLIENT_METHOD)
        sock = socket.create_connection((domain, port))
        ssl_conn = SSL.Connection(ctx, sock)
        ssl_conn.set_tlsext_host_name(domain.encode())
        ssl_conn.set_connect_state()
        ssl_conn.do_handshake()

        certs = ssl_conn.get_peer_cert_chain()
        logging.info(f"Server returned {len(certs)} certificate(s) for {domain}")

        certificate_chain = []
        for idx, cert in enumerate(certs):
            cryptography_cert = cert.to_cryptography()
            der = cryptography_cert.public_bytes(serialization.Encoding.DER)
            pem = ssl.DER_cert_to_PEM_cert(der)
            certificate_chain.append(pem)

            logging.debug(f"Certificate #{idx + 1} for {domain}:\n{pem}")

        ssl_conn.close()
        sock.close()
        return certificate_chain

    except SSL.Error as e:
        logging.error(f"SSL error while connecting to {domain}:{port} - {e}")
    except socket.error as e:
        logging.error(f"Socket error while connecting to {domain}:{port} - {e}")
    except Exception as e:
        logging.error(f"Unexpected error while connecting to {domain}:{port} - {e}")

    return []

def check_certificates(domain, alert_threshold):
    logging.debug(f"Retrieving certificate chain for domain: {domain}")
    certificate_chain = get_cert_chain(domain)
    if certificate_chain:
        logging.info(f"Successfully retrieved certificate chain for {domain}")
    else:
        logging.error(f"Failed to retrieve certificate chain for {domain}")

    logging.debug(f"Analyzing certificate for domain: {domain}")

    certs = []
    for pem in certificate_chain:
        cert = x509.load_pem_x509_certificate(pem.encode(), default_backend())
        certs.append(cert)

    conn = psycopg2.connect(dbname="certwatch", user="certuser", password=os.getenv("POSTGRES_PASSWORD"), host="cert-db")
    cursor = conn.cursor()

    for idx, cert in enumerate(certs):
        cert_type = 'leaf' if idx == 0 else ('root' if cert.issuer == cert.subject else f'intermediate_{idx}')
        logging.debug(f"Processing {cert_type} certificate: {cert.subject.rfc4514_string()}")
        expiry = cert.not_valid_after_utc
        expiry = expiry.replace(tzinfo=timezone.utc)
        issuer = cert.issuer.rfc4514_string()
        fingerprint = cert.fingerprint(hashes.SHA256()).hex()

        logging.debug(f"Certificate expiry: {expiry}, Issuer: {issuer}, Type: {cert_type}")
        logging.info("Domain: %s, Expiry: %s, Issuer: %s, Type: %s", domain, expiry, issuer, cert_type)

        # Check if the certificate is about to expire and alert only once
        now = datetime.now(timezone.utc)
        days_to_expiry = (expiry - now).days
        if days_to_expiry <= alert_threshold:
            alert_type = 'Expiry Alert'
            # Check if the alert for this fingerprint was already sent
            cursor.execute(
                "SELECT COUNT(*) FROM alerts WHERE domain = %s AND alert_type = %s AND fingerprint = %s",
                (domain, alert_type, fingerprint)
            )
            alert_exists = cursor.fetchone()[0] > 0

            if alert_exists:
                logging.info(f"Alert for {alert_type} with fingerprint {fingerprint} already sent. Skipping email.")
            else:
                alert_message = f"ALERT: {cert_type} certificate for {domain} is expiring in {days_to_expiry} days!"
                logging.info(alert_message)
                send_alert(
                    f"Certificate Expiry Alert: {domain}",
                    f"The {cert_type} certificate for {domain} is expiring in {days_to_expiry} days."
                )

                # Log the alert into the alerts table
                cursor.execute(
                    "INSERT INTO alerts (domain, alert_type, message, fingerprint, created_at) VALUES (%s, %s, %s, %s, NOW())",
                    (domain, 'Expiry Alert', alert_message, fingerprint)
                )
                conn.commit()

        # Check for issuer or fingerprint changes
        logging.debug(f"Checking for changes in {cert_type} certificate")

        # Query the last stored certificate details
        cursor.execute(
            "SELECT issuer, fingerprint FROM certificates WHERE domain = %s AND cert_type = %s ORDER BY last_checked DESC LIMIT 1",
            (domain, cert_type)
        )
        result = cursor.fetchone()

        if result:
            last_issuer, last_fingerprint = result
            if last_issuer != issuer:
                alert_type = 'Issuer Change'
                # Check if the alert for this fingerprint was already sent
                cursor.execute(
                    "SELECT COUNT(*) FROM alerts WHERE domain = %s AND alert_type = %s AND fingerprint = %s",
                    (domain, alert_type, fingerprint)
                )
                alert_exists = cursor.fetchone()[0] > 0

                if alert_exists:
                    logging.info(f"Alert for {alert_type} with fingerprint {fingerprint} already sent. Skipping email.")
                else:
                    alert_message = f"ALERT: Issuer for {cert_type} certificate of {domain} has changed from {last_issuer} to {issuer}!"
                    logging.info(alert_message)
                    send_alert(
                        f"Certificate Alert: Issuer Change for {domain}",
                        f"The issuer for the {cert_type} certificate of {domain} has changed.\n\nOld Issuer: {last_issuer}\nNew Issuer: {issuer}"
                    )

                    # Log the alert into the alerts table
                    cursor.execute(
                        "INSERT INTO alerts (domain, alert_type, message, fingerprint, created_at) VALUES (%s, %s, %s, %s, NOW())",
                        (domain, 'Issuer Change', alert_message, fingerprint)
                    )
                    conn.commit()

            if last_fingerprint != fingerprint:
                alert_type = 'Fingerprint Change'
                # Check if the alert for this fingerprint was already sent
                cursor.execute(
                    "SELECT COUNT(*) FROM alerts WHERE domain = %s AND alert_type = %s AND fingerprint = %s",
                    (domain, alert_type, fingerprint)
                )
                alert_exists = cursor.fetchone()[0] > 0

                if alert_exists:
                    logging.info(f"Alert for {alert_type} with fingerprint {fingerprint} already sent. Skipping email.")
                else:
                    alert_message = f"ALERT: Fingerprint for {cert_type} certificate of {domain} has changed!"
                    logging.info(alert_message)
                    send_alert(
                        f"Certificate Alert: Fingerprint Change for {domain}",
                        f"The fingerprint for the {cert_type} certificate of {domain} has changed.\n\nOld Fingerprint: {last_fingerprint}\nNew Fingerprint: {fingerprint}"
                    )

                    # Log the alert into the alerts table
                    cursor.execute(
                        "INSERT INTO alerts (domain, alert_type, message, fingerprint, created_at) VALUES (%s, %s, %s, %s, NOW())",
                        (domain, 'Fingerprint Change', alert_message, fingerprint)
                    )
                    conn.commit()

        pem_certificate = pem

        # Store the current certificate details in the database, including the PEM certificate
        cursor.execute(
            "INSERT INTO certificates (domain, expiry_date, issuer, fingerprint, cert_type, pem_certificate, last_checked) VALUES (%s, %s, %s, %s, %s, %s, NOW())",
            (domain, expiry, issuer, fingerprint, cert_type, pem_certificate)
        )
        conn.commit()
        logging.debug("Database updated with %s certificate details", cert_type)
    cursor.close()
    conn.close()