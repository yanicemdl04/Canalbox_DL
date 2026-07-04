from django.core.management.base import BaseCommand

from scripts.generate_project_pdf import build_pdf


class Command(BaseCommand):
    help = "Génère docs/CanalBox_Documentation.pdf (documentation colorée du projet)."

    def handle(self, *args, **options):
        path = build_pdf()
        self.stdout.write(self.style.SUCCESS(f"PDF généré : {path}"))
