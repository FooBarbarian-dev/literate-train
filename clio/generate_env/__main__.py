"""Entry point for the Clio environment generator.

Usage:
    python -m generate_env [--letsencrypt]

Generates self-signed TLS certificates and .env files with random secrets
for all Clio platform services.
"""

import argparse
import sys
from pathlib import Path

from generate_env.certs import generate_certs
from generate_env.env_writer import write_env_files


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate certificates and .env files for the Clio platform.",
    )
    parser.add_argument(
        "--letsencrypt",
        action="store_true",
        default=False,
        help="Configure for Let's Encrypt certificate paths instead of self-signed certs.",
    )
    args = parser.parse_args()

    # Resolve the project root (one level up from generate_env/)
    base_dir = Path(__file__).resolve().parent.parent

    print("Clio Environment Generator")
    print("=" * 40)

    # --- Certificates ---
    print("\n[1/2] Generating TLS certificates...")
    generate_certs(base_dir)

    # --- .env files ---
    print("\n[2/2] Generating .env files...")
    letsencrypt_cert = ""
    letsencrypt_key = ""
    if args.letsencrypt:
        letsencrypt_cert = "/etc/letsencrypt/live/localhost/fullchain.pem"
        letsencrypt_key = "/etc/letsencrypt/live/localhost/privkey.pem"

    write_env_files(
        base_dir,
        letsencrypt_cert_path=letsencrypt_cert,
        letsencrypt_key_path=letsencrypt_key,
    )

    print("\n" + "=" * 40)
    print("Setup complete! You can now run:")
    print("  docker compose up -d")


if __name__ == "__main__":
    main()
