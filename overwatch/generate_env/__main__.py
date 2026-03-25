"""Entry point for the Overwatch environment generator.

Usage:
    python -m generate_env

Generates .env files with random secrets for all Overwatch platform services.

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

    print("Overwatch Environment Generator")
    print("=" * 40)

    print("\nGenerating .env files...")
    write_env_files(base_dir)

    # Read back the generated passwords so the user can see them
    backend_env_path = base_dir / "backend" / ".env"
    admin_pw = ""
    user_pw = ""
    for line in backend_env_path.read_text().splitlines():
        if line.startswith("ADMIN_PASSWORD="):
            admin_pw = line.split("=", 1)[1]
        elif line.startswith("USER_PASSWORD="):
            user_pw = line.split("=", 1)[1]

    print("\n" + "=" * 40)
    print("Setup complete!\n")
    print("Credentials (also saved in backend/.env):")
    print(f"  Admin password: {admin_pw}")
    print(f"  User  password: {user_pw}")
    print("\nNext steps:")
    print("  docker compose up --build -d")
    print("  # (migrations and seeding run automatically)")
    print("")
    print("Optional — populate demo data:")
    print("  docker compose exec backend python manage.py seed_demo_data")


if __name__ == "__main__":
    main()
