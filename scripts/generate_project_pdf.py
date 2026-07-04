"""Génère docs/CanalBox_Documentation.pdf — document coloré du projet."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import Flowable


class CoverSpacer(Flowable):
    """Réserve toute la première page pour la couverture dessinée par canvas."""

    def wrap(self, availWidth, availHeight):
        return availWidth, availHeight

    def draw(self):
        pass

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT = BASE_DIR / "docs" / "CanalBox_Documentation.pdf"

# Palette Canal Box
PINK = colors.HexColor("#ff2d78")
PINK_DARK = colors.HexColor("#e0155f")
PINK_SOFT = colors.HexColor("#fff0f6")
INK = colors.HexColor("#0f0f12")
SLATE = colors.HexColor("#4b5565")
MIST = colors.HexColor("#98a2b3")
POS = colors.HexColor("#12b76a")
NEG = colors.HexColor("#f04438")
NEU = colors.HexColor("#f79009")
WHITE = colors.white
GLASS = colors.HexColor("#f8f9fc")
DARK_BG = colors.HexColor("#1a1a1f")


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "CBTitle", parent=base["Title"],
            fontName="Helvetica-Bold", fontSize=28, textColor=WHITE,
            alignment=TA_CENTER, spaceAfter=8,
        ),
        "subtitle": ParagraphStyle(
            "CBSub", parent=base["Normal"],
            fontName="Helvetica", fontSize=13, textColor=colors.HexColor("#ffcce0"),
            alignment=TA_CENTER, spaceAfter=4,
        ),
        "h1": ParagraphStyle(
            "CBH1", parent=base["Heading1"],
            fontName="Helvetica-Bold", fontSize=20, textColor=PINK,
            spaceBefore=18, spaceAfter=10,
        ),
        "h2": ParagraphStyle(
            "CBH2", parent=base["Heading2"],
            fontName="Helvetica-Bold", fontSize=14, textColor=INK,
            spaceBefore=14, spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "CBBody", parent=base["Normal"],
            fontName="Helvetica", fontSize=10, textColor=SLATE,
            leading=15, spaceAfter=6,
        ),
        "bullet": ParagraphStyle(
            "CBBullet", parent=base["Normal"],
            fontName="Helvetica", fontSize=10, textColor=SLATE,
            leading=14, leftIndent=14, bulletIndent=0, spaceAfter=3,
        ),
        "caption": ParagraphStyle(
            "CBCap", parent=base["Normal"],
            fontName="Helvetica-Oblique", fontSize=9, textColor=MIST,
            spaceAfter=8,
        ),
        "tag": ParagraphStyle(
            "CBTag", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=9, textColor=PINK,
        ),
    }


def _cover_page(c: canvas.Canvas, doc):
    w, h = A4
    c.saveState()
    # Fond dégradé simulé
    c.setFillColor(DARK_BG)
    c.rect(0, 0, w, h, fill=1, stroke=0)
    c.setFillColor(PINK)
    c.circle(w * 0.85, h * 0.82, 90, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#ff2d7844"))
    c.circle(w * 0.12, h * 0.18, 60, fill=1, stroke=0)

    # Logo
    c.setFillColor(PINK)
    c.roundRect(w / 2 - 36, h / 2 + 60, 72, 72, 18, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 42)
    c.drawCentredString(w / 2, h / 2 + 82, "C")

    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 32)
    c.drawCentredString(w / 2, h / 2 + 10, "Canal Box")
    c.setFont("Helvetica", 14)
    c.setFillColor(colors.HexColor("#ffcce0"))
    c.drawCentredString(w / 2, h / 2 - 18, "Plateforme d'avis clients · Analyse LSTM")

    c.setFont("Helvetica", 11)
    c.setFillColor(MIST)
    c.drawCentredString(w / 2, h / 2 - 70, "Examen Deep Learning — Projet académique")
    c.drawCentredString(w / 2, h / 2 - 86, "Version 1.1 · Juillet 2026")

    # Badges stack
    badges = [("Django 5.2", PINK), ("SQLite", SLATE), ("LSTM", POS), ("Liquid Glass", NEU)]
    x = w / 2 - 130
    for label, col in badges:
        c.setFillColor(col)
        c.roundRect(x, 3.5 * cm, 58, 22, 6, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(x + 29, 3.5 * cm + 7, label)
        x += 66

    c.setFillColor(MIST)
    c.setFont("Helvetica", 8)
    c.drawCentredString(w / 2, 1.5 * cm, "Documentation générée automatiquement — Canal Box DL")
    c.restoreState()


def _header_footer(canvas_obj, doc):
    if canvas_obj.getPageNumber() == 1:
        return
    canvas_obj.saveState()
    w, _ = A4
    canvas_obj.setFillColor(PINK)
    canvas_obj.rect(0, A4[1] - 12 * mm, w, 3 * mm, fill=1, stroke=0)
    canvas_obj.setFillColor(SLATE)
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.drawString(2 * cm, 1 * cm, "Canal Box — Documentation technique")
    canvas_obj.drawRightString(w - 2 * cm, 1 * cm, f"Page {canvas_obj.getPageNumber()}")
    canvas_obj.restoreState()


def _colored_table(data, col_widths, header_color=PINK):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), header_color),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("TEXTCOLOR", (0, 1), (-1, -1), SLATE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, GLASS]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e4e7ec")),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    t.setStyle(TableStyle(style))
    return t


def _architecture_box(st):
    """Diagramme ASCII en tableau coloré."""
    rows = [
        [Paragraph("<b>COUCHE PRÉSENTATION</b>", st["tag"]),
         Paragraph("Templates Django · Tailwind · GSAP · Liquid Glass", st["body"])],
        [Paragraph("<b>COUCHE MÉTIER</b>", st["tag"]),
         Paragraph("views.py · review_service · stats_service · presenters", st["body"])],
        [Paragraph("<b>COUCHE IA</b>", st["tag"]),
         Paragraph("lstm_service → lstm_stub (actif) / lstm_keras (.h5)", st["body"])],
        [Paragraph("<b>COUCHE DONNÉES</b>", st["tag"]),
         Paragraph("SQLite · User · Category · Review · SentimentResult · InferenceLog", st["body"])],
    ]
    t = Table(rows, colWidths=[4.2 * cm, 12.8 * cm])
    colors_row = [PINK_SOFT, GLASS, colors.HexColor("#ecfdf3"), colors.HexColor("#f0f4ff")]
    cmds = [
        ("BOX", (0, 0), (-1, -1), 1, PINK),
        ("ROUNDEDCORNERS", [8, 8, 8, 8]),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    for i, bg in enumerate(colors_row):
        cmds.append(("BACKGROUND", (0, i), (-1, i), bg))
    t.setStyle(TableStyle(cmds))
    return t


def _flow_steps(st):
    steps = [
        ("1", "Client", "Rédige un avis (titre, texte, note, catégorie)", PINK),
        ("2", "Backend", "Enregistre en base (status: pending)", SLATE),
        ("3", "LSTM", "Analyse le texte → sentiment + confiance", POS),
        ("4", "Backend", "Met à jour (status: analyzed) + log inférence", SLATE),
        ("5", "Client", "Voit l'avis publié — sans étiquette IA", PINK_SOFT),
        ("6", "Admin", "Consulte sentiment, stats, modération", colors.HexColor("#1a1a1f")),
    ]
    rows = []
    for num, actor, desc, col in steps:
        badge = Table([[num]], colWidths=[0.8 * cm])
        badge.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), col),
            ("TEXTCOLOR", (0, 0), (-1, -1), WHITE if col != PINK_SOFT else PINK),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        rows.append([
            badge,
            Paragraph(f"<b>{actor}</b> — {desc}", st["body"]),
        ])
    t = Table(rows, colWidths=[1.2 * cm, 15.8 * cm])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def build_pdf():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    st = _styles()
    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
        title="Canal Box — Documentation",
        author="Équipe Deep Learning LSTM",
    )

    story = [CoverSpacer(), PageBreak()]
    story.append(Paragraph("Sommaire", st["h1"]))
    for item in [
        "1. Présentation du projet",
        "2. Architecture technique",
        "3. Flux de données (soumission d'avis)",
        "4. Modèle de données",
        "5. Structure des dossiers",
        "6. Pages de l'application",
        "7. Règles de sécurité & rôles",
        "8. Intégration LSTM",
        "9. Installation & commandes",
    ]:
        story.append(Paragraph(f"• {item}", st["bullet"]))
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=2, color=PINK, spaceAfter=12))

    # --- 1. Présentation ---
    story.append(Paragraph("1. Présentation du projet", st["h1"]))
    story.append(Paragraph(
        "Canal Box est une plateforme simulée d'avis clients pour un opérateur "
        "de services numériques (internet fibre, décodeur TV, assistance client, facturation). "
        "Chaque avis soumis est automatiquement analysé par un réseau LSTM qui prédit "
        "la polarité du texte : <b>positif</b>, <b>négatif</b> ou <b>neutre</b>.",
        st["body"],
    ))
    story.append(Spacer(1, 6))
    obj_data = [
        ["Objectif", "Description"],
        ["Collecte", "Permettre aux clients de publier et consulter des avis"],
        ["Analyse IA", "Classifier automatiquement chaque avis via LSTM"],
        ["Administration", "Tableau de bord, modération, logs, exports"],
        ["Confidentialité IA", "Les résultats LSTM visibles uniquement par les admins"],
    ]
    story.append(_colored_table(obj_data, [4 * cm, 13 * cm]))
    story.append(Spacer(1, 12))

    # --- 2. Architecture ---
    story.append(Paragraph("2. Architecture technique", st["h1"]))
    story.append(Paragraph(
        "L'application repose sur une architecture <b>monolithique Django</b> : "
        "templates, logique métier, inférence LSTM et persistance SQLite dans un seul projet.",
        st["body"],
    ))
    story.append(Spacer(1, 8))
    story.append(_architecture_box(st))
    story.append(Spacer(1, 10))
    stack_data = [
        ["Composant", "Technologie", "Rôle"],
        ["Backend", "Django 5.2 + ORM", "Vues, auth, services métier"],
        ["Base de données", "SQLite", "Persistance locale des avis et résultats IA"],
        ["Frontend", "Django Templates + Tailwind", "Interface Liquid Glass responsive"],
        ["Animations", "GSAP + ScrollTrigger", "Transitions et micro-interactions"],
        ["IA (actif)", "lstm_stub.py", "Heuristiques FR en attendant le modèle"],
        ["IA (futur)", "lstm_keras.py + .h5", "Modèle TensorFlow/Keras entraîné"],
    ]
    story.append(_colored_table(stack_data, [3.5 * cm, 5.5 * cm, 8 * cm], header_color=INK))
    story.append(PageBreak())

    # --- 3. Flux ---
    story.append(Paragraph("3. Flux de données", st["h1"]))
    story.append(Paragraph(
        "À chaque soumission d'avis, le pipeline suivant s'exécute de manière transparente "
        "pour le client :", st["body"]))
    story.append(Spacer(1, 8))
    story.append(_flow_steps(st))
    story.append(Spacer(1, 14))

    # Sentiment legend
    leg = Table([
        [Paragraph("<b>Positif</b>", ParagraphStyle("lp", fontName="Helvetica-Bold", fontSize=9, textColor=WHITE)),
         Paragraph("<b>Négatif</b>", ParagraphStyle("ln", fontName="Helvetica-Bold", fontSize=9, textColor=WHITE)),
         Paragraph("<b>Neutre</b>", ParagraphStyle("lu", fontName="Helvetica-Bold", fontSize=9, textColor=WHITE))],
    ], colWidths=[5.67 * cm, 5.67 * cm, 5.66 * cm])
    leg.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), POS),
        ("BACKGROUND", (1, 0), (1, 0), NEG),
        ("BACKGROUND", (2, 0), (2, 0), NEU),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(leg)
    story.append(Spacer(1, 16))

    # --- 4. Modèle de données ---
    story.append(Paragraph("4. Modèle de données", st["h1"]))
    db_data = [
        ["Table", "Champs clés", "Description"],
        ["users", "email, role, plan, status", "Comptes client et administrateur"],
        ["categories", "name, slug, description, icon", "Services Canal Box évaluables"],
        ["reviews", "user_id, title, content, rating, status", "Avis clients soumis"],
        ["sentiment_results", "sentiment, confidence, prob_*", "Résultat LSTM par avis"],
        ["inference_logs", "status, latency_ms, model_version", "Journal des inférences"],
    ]
    story.append(_colored_table(db_data, [3.5 * cm, 5.5 * cm, 8 * cm], header_color=PINK_DARK))
    story.append(Spacer(1, 12))

    # --- 5. Structure ---
    story.append(Paragraph("5. Structure des dossiers", st["h1"]))
    tree = """canalbox/          → settings.py, urls.py
core/
  models.py          → User, Category, Review, SentimentResult
  views.py           → 30+ vues (public, client, admin)
  presenters.py      → ORM → dicts pour templates
  services/          → review_service, stats_service
  ml/                → lstm_service, lstm_stub, lstm_keras
  management/        → seed_canalbox
templates/           → public/, client/, adminpanel/, partials/
static/              → canalbox.css, canalbox.js
ml_models/           → lstm_sentiment.h5 (à venir)
docs/                → CanalBox_Documentation.pdf"""
    story.append(Paragraph(f"<font face='Courier' size='9' color='#4b5565'>{tree.replace(chr(10), '<br/>')}</font>", st["body"]))
    story.append(PageBreak())

    # --- 6. Pages ---
    story.append(Paragraph("6. Pages de l'application", st["h1"]))

    story.append(Paragraph("Espace public", st["h2"]))
    pub = [
        ["URL", "Page", "Accès"],
        ["/", "Landing — présentation Canal Box", "Tous"],
        ["/connexion/", "Connexion e-mail / mot de passe", "Visiteurs"],
        ["/inscription/", "Création de compte client", "Visiteurs"],
        ["/mot-de-passe-oublie/", "Réinitialisation mot de passe", "Visiteurs"],
    ]
    story.append(_colored_table(pub, [4 * cm, 7.5 * cm, 5.5 * cm], header_color=colors.HexColor("#6941c6")))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Espace client", st["h2"]))
    cli = [
        ["URL", "Page", "Accès"],
        ["/espace/", "Tableau de bord personnel", "Client"],
        ["/espace/avis/", "Liste, recherche, filtres, pagination", "Client"],
        ["/espace/avis/nouveau/", "Formulaire de soumission d'avis", "Client"],
        ["/espace/avis/<id>/", "Détail d'un avis (sans IA)", "Client"],
        ["/espace/profil/", "Profil et statistiques", "Client"],
        ["/espace/profil/modifier/", "Modification du profil", "Client"],
    ]
    story.append(_colored_table(cli, [4.5 * cm, 7 * cm, 5.5 * cm], header_color=PINK))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Console administrateur", st["h2"]))
    adm = [
        ["URL", "Page", "Accès"],
        ["/administration/", "Dashboard KPI + graphiques sentiments", "Admin"],
        ["/administration/avis/", "Liste avec sentiment & confiance LSTM", "Admin"],
        ["/administration/avis/<id>/", "Détail + distribution softmax", "Admin"],
        ["/administration/moderation/", "Avis signalés (confiance faible)", "Admin"],
        ["/administration/utilisateurs/", "Gestion comptes (suspendre)", "Admin"],
        ["/administration/categories/", "CRUD catégories de services", "Admin"],
        ["/administration/logs/", "Journal inférences (latence, erreurs)", "Admin"],
        ["/administration/exports/csv/", "Export CSV des avis analysés", "Admin"],
        ["/administration/exports/pdf/", "Export rapport analytique", "Admin"],
    ]
    story.append(_colored_table(adm, [5 * cm, 6.5 * cm, 5.5 * cm], header_color=INK))
    story.append(PageBreak())

    # --- 7. Sécurité ---
    story.append(Paragraph("7. Règles de sécurité & rôles", st["h1"]))
    rules = [
        ["Règle", "Implémentation"],
        ["IA invisible côté client", "review_to_dict(include_ia=False) dans toutes les vues client"],
        ["Accès admin protégé", "Décorateur admin_required + role == admin"],
        ["Comptes suspendus", "Vérification status avant chaque action"],
        ["Seuil de confiance", "MIN_CONFIDENCE_THRESHOLD → flagged automatique"],
        ["Validation entrées", "Longueur min titre/contenu, note 1-5, e-mail unique"],
    ]
    story.append(_colored_table(rules, [5.5 * cm, 11.5 * cm], header_color=NEG))
    story.append(Spacer(1, 14))

    # --- 8. LSTM ---
    story.append(Paragraph("8. Intégration du modèle LSTM", st["h1"]))
    story.append(Paragraph(
        "Le stub actuel (<font color='#12b76a'><b>lstm_stub.py</b></font>) utilise des heuristiques "
        "sur mots-clés français. Pour brancher le modèle entraîné :", st["body"]))
    steps_lstm = [
        "1. Exporter le modèle depuis Jupyter (format .h5 ou SavedModel)",
        "2. Placer le fichier dans ml_models/lstm_sentiment.h5",
        "3. Implémenter predict() dans core/ml/lstm_keras.py",
        "4. Changer LSTM_BACKEND = 'keras' dans canalbox/settings.py",
    ]
    for s in steps_lstm:
        story.append(Paragraph(s, st["bullet"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "<b>Contrainte cahier des charges :</b> temps d'inférence &lt; 3 secondes par avis.",
        st["caption"],
    ))

    # --- 9. Installation ---
    story.append(Paragraph("9. Installation & commandes", st["h1"]))
    cmds = [
        ["Commande", "Description"],
        ["pip install -r requirements.txt", "Installer les dépendances"],
        ["python manage.py migrate", "Créer les tables SQLite"],
        ["python manage.py seed_canalbox", "Insérer données de démonstration"],
        ["python manage.py runserver", "Lancer le serveur de développement"],
        ["python manage.py generate_project_pdf", "Régénérer ce document"],
    ]
    story.append(_colored_table(cmds, [7 * cm, 10 * cm], header_color=POS))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "<b>Comptes démo :</b> yanice.client@canalbox.cd / david.admin@canalbox.cd — mot de passe <b>demo1234</b>",
        st["body"],
    ))
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="30%", thickness=3, color=PINK, spaceAfter=8))
    story.append(Paragraph(
        "© 2026 Canal Box — Équipe Deep Learning LSTM · Document confidentiel — Usage académique",
        ParagraphStyle("foot", fontName="Helvetica-Oblique", fontSize=8, textColor=MIST, alignment=TA_CENTER),
    ))

    doc.build(story, onFirstPage=_cover_page, onLaterPages=_header_footer)
    return OUTPUT


if __name__ == "__main__":
    path = build_pdf()
    print(f"PDF généré : {path}")
