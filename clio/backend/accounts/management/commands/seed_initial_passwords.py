import environ

env = environ.Env()

from django.core.management.base import BaseCommand

from accounts.hashers import hash_password
from common.redis_client import get_encrypted_redis


class Command(BaseCommand):
    help = "Hash initial admin/user passwords and store in Redis"

    def handle(self, *args, **options):
        redis_client = get_encrypted_redis()

        admin_password = env("ADMIN_PASSWORD", default="")
        if admin_password:
            hashed = hash_password(admin_password)
            redis_client.set("initial:admin_password", hashed)
            self.stdout.write(self.style.SUCCESS("Initial admin password hashed and stored"))

        user_password = env("USER_PASSWORD", default="")
        if user_password:
            hashed = hash_password(user_password)
            redis_client.set("initial:user_password", hashed)
            self.stdout.write(self.style.SUCCESS("Initial user password hashed and stored"))
