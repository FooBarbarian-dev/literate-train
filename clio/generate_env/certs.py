"""Self-signed certificate generation for Clio platform services."""

import datetime
import os
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def _generate_key() -> rsa.RSAPrivateKey:
    """Generate a 4096-bit RSA private key."""
    return rsa.generate_private_key(public_exponent=65537, key_size=4096)


def _write_key(key: rsa.RSAPrivateKey, path: Path) -> None:
    """Write a private key to a PEM file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    os.chmod(path, 0o600)


def _write_cert(cert: x509.Certificate, path: Path) -> None:
    """Write a certificate to a PEM file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))


def _build_ca(
    validity_days: int = 365,
) -> tuple[rsa.RSAPrivateKey, x509.Certificate]:
    """Generate a self-signed CA certificate and key."""
    key = _generate_key()
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Clio Platform"),
            x509.NameAttribute(NameOID.COMMON_NAME, "Clio Root CA"),
        ]
    )
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=validity_days))
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_cert_sign=True,
                crl_sign=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .sign(key, hashes.SHA256())
    )
    return key, cert


def _build_server_cert(
    ca_key: rsa.RSAPrivateKey,
    ca_cert: x509.Certificate,
    common_name: str,
    san_dns_names: list[str],
    validity_days: int = 365,
) -> tuple[rsa.RSAPrivateKey, x509.Certificate]:
    """Generate a server certificate signed by the CA."""
    key = _generate_key()
    subject = x509.Name(
        [
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Clio Platform"),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ]
    )
    now = datetime.datetime.now(datetime.timezone.utc)
    san_entries: list[x509.GeneralName] = [
        x509.DNSName(name) for name in san_dns_names
    ]
    san_entries.append(x509.IPAddress(
        __import__("ipaddress").IPv4Address("127.0.0.1")
    ))
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=validity_days))
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )
        .add_extension(
            x509.SubjectAlternativeName(san_entries),
            critical=False,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                content_commitment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage(
                [
                    x509.oid.ExtendedKeyUsageOID.SERVER_AUTH,
                    x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH,
                ]
            ),
            critical=False,
        )
        .sign(ca_key, hashes.SHA256())
    )
    return key, cert


def generate_certs(base_dir: Path) -> None:
    """Generate all certificates for the Clio platform.

    Creates the following structure under *base_dir*/certs/:
        ca.crt, ca.key          - Certificate Authority
        server.crt, server.key  - General server certificate
        redis/                  - Redis TLS certs (redis.crt, redis.key, ca.crt)
        postgres/               - Postgres SSL certs (server.crt, server.key)
    """
    certs_dir = base_dir / "certs"
    certs_dir.mkdir(parents=True, exist_ok=True)

    san_dns_names = [
        "localhost",
        "backend",
        "relation-service",
        "redis",
        "db",
    ]

    # --- CA ---
    ca_key, ca_cert = _build_ca()
    _write_key(ca_key, certs_dir / "ca.key")
    _write_cert(ca_cert, certs_dir / "ca.crt")

    # --- Server cert ---
    server_key, server_cert = _build_server_cert(
        ca_key, ca_cert, "clio-server", san_dns_names
    )
    _write_key(server_key, certs_dir / "server.key")
    _write_cert(server_cert, certs_dir / "server.crt")

    # --- Redis certs ---
    redis_key, redis_cert = _build_server_cert(
        ca_key, ca_cert, "redis", san_dns_names
    )
    redis_dir = certs_dir / "redis"
    _write_key(redis_key, redis_dir / "redis.key")
    _write_cert(redis_cert, redis_dir / "redis.crt")
    _write_cert(ca_cert, redis_dir / "ca.crt")

    # --- Postgres certs ---
    pg_key, pg_cert = _build_server_cert(
        ca_key, ca_cert, "postgres", san_dns_names
    )
    pg_dir = certs_dir / "postgres"
    _write_key(pg_key, pg_dir / "server.key")
    _write_cert(pg_cert, pg_dir / "server.crt")

    print(f"  Certificates written to {certs_dir}/")
