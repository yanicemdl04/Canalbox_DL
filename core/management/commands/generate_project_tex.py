from django.core.management.base import BaseCommand
from pathlib import Path
import shutil
import subprocess


class Command(BaseCommand):
    help = "Compile docs/CanalBox_Documentation.tex en PDF (nécessite pdflatex)."

    def handle(self, *args, **options):
        tex = Path(__file__).resolve().parent.parent.parent.parent / "docs" / "CanalBox_Documentation.tex"
        docs_dir = tex.parent

        if not tex.exists():
            self.stderr.write(self.style.ERROR(f"Fichier introuvable : {tex}"))
            return

        pdflatex = shutil.which("pdflatex")
        if not pdflatex:
            self.stdout.write(self.style.WARNING(
                "pdflatex non installé — le fichier .tex a été créé dans docs/.\n"
                "Installez TeX Live puis lancez :\n"
                "  cd docs && pdflatex CanalBox_Documentation.tex"
            ))
            self.stdout.write(self.style.SUCCESS(f"Source LaTeX : {tex}"))
            return

        for _ in range(2):
            result = subprocess.run(
                [pdflatex, "-interaction=nonstopmode", tex.name],
                cwd=docs_dir, capture_output=True, text=True,
            )
            if result.returncode != 0:
                self.stderr.write(result.stdout[-2000:] if result.stdout else "")
                self.stderr.write(self.style.ERROR("Échec de la compilation LaTeX."))
                return

        pdf = docs_dir / "CanalBox_Documentation.pdf"
        self.stdout.write(self.style.SUCCESS(f"PDF compilé depuis LaTeX : {pdf}"))
