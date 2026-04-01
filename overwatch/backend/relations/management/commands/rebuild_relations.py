"""Management command to rebuild all relations from existing logs."""

from django.core.management.base import BaseCommand

from logs.models import Log
from relations.models import Relation
from relations.services import rebuild_all_relations


class Command(BaseCommand):
    help = "Rebuild all entity relations from existing log entries"

    def handle(self, *args, **options):
        log_count = Log.objects.count()
        self.stdout.write(f"Processing {log_count} logs...")

        results = rebuild_all_relations()

        total = Relation.objects.count()
        for rtype, count in results.items():
            self.stdout.write(f"  Created {count} {rtype} relations")
        self.stdout.write(self.style.SUCCESS(f"Total: {total} relations"))
