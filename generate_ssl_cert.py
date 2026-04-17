#!/usr/bin/env python3
"""
Generate self-signed SSL certificate using Python cryptography library
"""
from pathlib import Path
from datetime import datetime, timedelta
import ipaddress

try:
    from cryptography import x509
    from cryptography.x509.oid import NameOID, ExtensionOID
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
except ImportError:
    print("Installing cryptography...")
    import subprocess
    subprocess.check_call(["pip", "install", "cryptography"])
    from cryptography import x509
    from cryptography.x509.oid import NameOID, ExtensionOID
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization

# Setup paths
ssl_dir = Path(__file__).parent / "nginx" / "ssl"
ssl_dir.mkdir(parents=True, exist_ok=True)

cert_file = ssl_dir / "self-signed.crt"
key_file = ssl_dir / "self-signed.key"

print(f"🔐 Generating SSL certificate in {ssl_dir}")

# Generate private key
print("  → Generating RSA private key (2048 bits)...")
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend()
)

# Generate certificate
print("  → Creating X.509 certificate...")
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"California"),
    x509.NameAttribute(NameOID.LOCALITY_NAME, u"San Francisco"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Sports Prediction"),
    x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),
])

cert = x509.CertificateBuilder().subject_name(
    subject
).issuer_name(
    issuer
).public_key(
    private_key.public_key()
).serial_number(
    x509.random_serial_number()
).not_valid_before(
    datetime.utcnow()
).not_valid_after(
    datetime.utcnow() + timedelta(days=365)
).add_extension(
    x509.SubjectAlternativeName([
        x509.DNSName(u"localhost"),
        x509.DNSName(u"*.localhost"),
        x509.DNSName(u"127.0.0.1"),
    ]),
    critical=False,
).add_extension(
    x509.BasicConstraints(ca=False, path_length=None),
    critical=True,
).sign(private_key, hashes.SHA256(), default_backend())

# Write certificate
print("  → Writing certificate file...")
with open(cert_file, "wb") as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))

# Write private key
print("  → Writing private key file...")
with open(key_file, "wb") as f:
    f.write(private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ))

print(f"\n✅ SSL certificate generated successfully!")
print(f"   Certificate: {cert_file} ({cert_file.stat().st_size} bytes)")
print(f"   Private Key: {key_file} ({key_file.stat().st_size} bytes)")
print(f"   Valid for: 365 days")
print(f"   CN: localhost")
