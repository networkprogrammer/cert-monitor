# Import necessary modules for SSL/TLS certificate handling and parsing
import socket
from OpenSSL import SSL, crypto
from cryptography import x509
from cryptography.hazmat.backends import default_backend
import base64

# Function to convert DER-encoded certificate bytes to PEM format
def der_to_pem(der_bytes):
    # Encode the DER bytes to Base64
    b64 = base64.encodebytes(der_bytes).decode('ascii')
    # Add PEM headers and format the Base64 string into 64-character lines
    lines = ['-----BEGIN CERTIFICATE-----']
    lines += [b64[i:i+64] for i in range(0, len(b64), 64)]
    lines.append('-----END CERTIFICATE-----')
    return '\n'.join(lines)

# Function to parse a DER-encoded certificate and extract its details
def parse_cert(der_bytes):
    # Load the certificate using the cryptography library
    cert = x509.load_der_x509_certificate(der_bytes, default_backend())
    try:
        # Extract Subject Alternative Names (SANs) if available
        sans = cert.extensions.get_extension_for_class(
            x509.SubjectAlternativeName
        ).value.get_values_for_type(x509.DNSName)
    except x509.ExtensionNotFound:
        # If SANs are not found, return an empty list
        sans = []
    return {
        "Subject": cert.subject.rfc4514_string(),
        "Issuer": cert.issuer.rfc4514_string(),
        "Serial Number": hex(cert.serial_number),
        "Valid From": cert.not_valid_before,
        "Valid To": cert.not_valid_after,
        "SANs": sans
    }

# Function to retrieve and parse the certificate chain from a server
def get_cert_chain(hostname, port=443):
    # Create an SSL context for a client connection
    ctx = SSL.Context(SSL.TLS_CLIENT_METHOD)
    # Establish a socket connection to the server
    sock = socket.create_connection((hostname, port))
    ssl_conn = SSL.Connection(ctx, sock)
    # Set the hostname for Server Name Indication (SNI)
    ssl_conn.set_tlsext_host_name(hostname.encode())
    ssl_conn.set_connect_state()
    # Perform the SSL/TLS handshake
    ssl_conn.do_handshake()

    # Retrieve the certificate chain from the server
    certs = ssl_conn.get_peer_cert_chain()
    print(f"\n✅ Server returned {len(certs)} certificate(s):\n")

    for idx, cert in enumerate(certs):
        # Convert the certificate to DER format
        der = crypto.dump_certificate(crypto.FILETYPE_ASN1, cert)
        # Convert the DER certificate to PEM format
        pem = der_to_pem(der)
        # Parse the certificate details
        parsed = parse_cert(der)

        print(f"🔒 Certificate #{idx + 1}")
        print(pem)
        print("🔍 Parsed Info:")
        for k, v in parsed.items():
            print(f"   {k}: {v}")
        print("\n" + "-" * 80)

    # Close the SSL/TLS and socket connections
    ssl_conn.close()
    sock.close()

# Main entry point for the script
if __name__ == "__main__":
    # Retrieve and display the certificate chain for the specified hostname
    get_cert_chain("example.com")