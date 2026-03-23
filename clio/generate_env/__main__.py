"""Entry point for the Clio environment generator.

Usage:
    python -m generate_env

Generates .env files with random secrets for all Clio platform services.

NOTE (PoC): TLS certificate generation has been removed for simplicity.
In production, generate self-signed or Let's Encrypt certificates and
re-enable SSL on Redis, PostgreSQL, and nginx. See certs.py for the
original certificate generation logic.
"""

from pathlib import Path

from generate_env.env_writer import write_env_files


def main() -> None:
    # Resolve the project root (one level up from generate_env/)
    base_dir = Path(__file__).resolve().parent.parent

    print("Clio Environment Generator")
    print("=" * 40)

    print("\nGenerating .env files...")
    write_env_files(base_dir)

    print("\n" + "=" * 40)
    print("Setup complete! You can now run:")
    print("  docker compose up -d")


if __name__ == "__main__":
    main()
