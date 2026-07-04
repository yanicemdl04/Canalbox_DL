"""Jeux de données statiques pour la commande seed_canalbox.

Les vues utilisent l'ORM Django — ce module n'est plus consommé à l'exécution.
"""
from datetime import datetime, timedelta

# --- Utilisateurs de démonstration -----------------------------------------
DEMO_USERS = {
    "client": {
        "id": 7,
        "name": "Yanice Mundele",
        "email": "yanice.client@canalbox.cd",
        "role": "client",
        "initials": "YM",
        "plan": "Canal Box Fibre 200",
        "member_since": "Mars 2025",
        "avatar_color": "from-pink-500 to-rose-400",
    },
    "admin": {
        "id": 1,
        "name": "David Débuze",
        "email": "david.admin@canalbox.cd",
        "role": "admin",
        "initials": "DD",
        "plan": "Administrateur plateforme",
        "member_since": "Janvier 2025",
        "avatar_color": "from-neutral-800 to-neutral-600",
    },
}

CATEGORIES = [
    {"id": 1, "name": "Internet Fibre", "slug": "internet", "description": "Connexion internet, débit, stabilité", "count": 1284, "icon": "wifi"},
    {"id": 2, "name": "Décodeur TV", "slug": "tv", "description": "Bouquet TV, décodeur, replay", "count": 856, "icon": "tv"},
    {"id": 3, "name": "Assistance client", "slug": "sav", "description": "Support technique et relation client", "count": 642, "icon": "headset"},
    {"id": 4, "name": "Facturation", "slug": "facturation", "description": "Factures, paiements, abonnements", "count": 398, "icon": "receipt"},
]

_AUTHORS = [
    ("Grâce Kabongo", "GK"), ("Joël Lumpungu", "JL"), ("Junior Bakana", "JB"),
    ("Estelle Dyese", "ED"), ("Elie Ntwari", "EN"), ("Djessy Mbala", "DM"),
    ("Yvette Kanku", "YK"), ("Néhémie Musekedi", "NM"), ("Kevin Bitubisha", "KB"),
    ("Mike Unga", "MU"), ("Jonathan Mutombo", "JM"), ("José Siku", "JS"),
]

_TITLES = [
    ("Connexion enfin stable depuis la fibre", "Depuis l'installation de la fibre Canal Box, ma connexion est stable jour et nuit. Le technicien a été très professionnel et le débit dépasse mes attentes.", 5, 1, "positif", 0.97),
    ("Décodeur qui redémarre tout seul", "Le décodeur redémarre plusieurs fois par soirée, impossible de regarder un film en entier. C'est vraiment frustrant pour un service payant.", 2, 2, "negatif", 0.93),
    ("Service correct sans plus", "L'abonnement fonctionne globalement. Rien d'exceptionnel mais je n'ai pas de gros problème à signaler pour le moment.", 3, 1, "neutre", 0.81),
    ("Assistance réactive et à l'écoute", "J'ai contacté le SAV pour un souci de facturation, réponse en moins de 10 minutes et problème résolu. Bravo à l'équipe support.", 5, 3, "positif", 0.95),
    ("Facture incompréhensible ce mois-ci", "Ma facture a doublé sans explication. J'ai appelé trois fois sans obtenir de réponse claire. Très déçu du suivi.", 1, 4, "negatif", 0.96),
    ("Bonne qualité d'image en 4K", "Les chaînes en 4K sont superbes sur mon téléviseur. Le catalogue replay est complet et l'interface du décodeur reste fluide.", 5, 2, "positif", 0.92),
    ("Débit qui chute le soir", "En journée tout va bien mais aux heures de pointe le débit s'effondre. J'aimerais comprendre pourquoi.", 2, 1, "negatif", 0.88),
    ("Installation rapide et propre", "Rendez-vous respecté, installation en une heure, câblage soigné. Rien à redire sur la prestation d'installation.", 4, 1, "positif", 0.9),
    ("Interface du décodeur perfectible", "Le contenu est bon mais naviguer dans les menus est parfois lent. Une mise à jour logicielle serait bienvenue.", 3, 2, "neutre", 0.76),
    ("Prélèvement en double", "J'ai été prélevé deux fois ce mois-ci. Le remboursement est en cours mais cela crée de la méfiance.", 2, 4, "negatif", 0.9),
    ("Meilleur opérateur de la région", "Après avoir testé la concurrence, Canal Box reste le plus fiable chez moi. Je recommande sans hésiter.", 5, 1, "positif", 0.98),
    ("Support difficile à joindre", "Temps d'attente très long au téléphone. Une fois en ligne, l'agent était compétent mais l'attente gâche l'expérience.", 3, 3, "neutre", 0.72),
]


def _build_reviews():
    reviews = []
    base = datetime(2026, 7, 4, 14, 0)
    for i, (title, content, rating, cat_id, sentiment, conf) in enumerate(_TITLES):
        author, initials = _AUTHORS[i % len(_AUTHORS)]
        cat = next(c for c in CATEGORIES if c["id"] == cat_id)
        created = base - timedelta(hours=i * 7 + 3, minutes=i * 11)
        reviews.append({
            "id": 100 + i,
            "title": title,
            "content": content,
            "excerpt": content[:120] + ("…" if len(content) > 120 else ""),
            "rating": rating,
            "author": author,
            "initials": initials,
            "category": cat,
            "created_at": created,
            "created_label": created.strftime("%d %b %Y · %Hh%M"),
            "status": "analysé",
            # Champs IA (ADMIN uniquement — jamais exposés au client)
            "sentiment": sentiment,
            "confidence": conf,
            "processing_ms": 420 + (i * 37) % 900,
            "flagged": i in (1, 4, 9),
        })
    return reviews


REVIEWS = _build_reviews()


def get_review(review_id):
    for r in REVIEWS:
        if r["id"] == int(review_id):
            return r
    return None


# --- Statistiques admin ------------------------------------------------------
def dashboard_stats():
    total = len(REVIEWS)
    pos = sum(1 for r in REVIEWS if r["sentiment"] == "positif")
    neg = sum(1 for r in REVIEWS if r["sentiment"] == "negatif")
    neu = sum(1 for r in REVIEWS if r["sentiment"] == "neutre")
    avg = round(sum(r["rating"] for r in REVIEWS) / total, 2)
    return {
        "total": 3180,
        "total_label": "3 180",
        "positive": pos, "negative": neg, "neutral": neu,
        "positive_pct": round(pos / total * 100),
        "negative_pct": round(neg / total * 100),
        "neutral_pct": round(neu / total * 100),
        "avg_rating": avg,
        "avg_confidence": 0.91,
        "avg_latency": 612,
        "satisfaction": 78,
        # Séries pour graphiques (7 derniers jours) — valeurs en % de hauteur
        "trend": [
            {"day": "Lun", "pos": 58, "neg": 25, "neu": 17},
            {"day": "Mar", "pos": 70, "neg": 19, "neu": 21},
            {"day": "Mer", "pos": 66, "neg": 30, "neu": 15},
            {"day": "Jeu", "pos": 86, "neg": 16, "neu": 25},
            {"day": "Ven", "pos": 80, "neg": 22, "neu": 19},
            {"day": "Sam", "pos": 98, "neg": 12, "neu": 22},
            {"day": "Dim", "pos": 92, "neg": 15, "neu": 18},
        ],
        "by_category": [
            {"name": "Internet Fibre", "value": 1284, "pct": 40, "sentiment": 82},
            {"name": "Décodeur TV", "value": 856, "pct": 27, "sentiment": 74},
            {"name": "Assistance client", "value": 642, "pct": 20, "sentiment": 69},
            {"name": "Facturation", "value": 398, "pct": 13, "sentiment": 58},
        ],
    }


INFERENCE_LOGS = [
    {"id": 9021, "review_id": 111, "status": "succès", "sentiment": "positif", "confidence": 0.98, "latency": 512, "ts": "04 Juil · 13h58", "model": "lstm-fr-v2.3"},
    {"id": 9020, "review_id": 110, "status": "succès", "sentiment": "negatif", "confidence": 0.9, "latency": 604, "ts": "04 Juil · 12h41", "model": "lstm-fr-v2.3"},
    {"id": 9019, "review_id": 109, "status": "succès", "sentiment": "neutre", "confidence": 0.76, "latency": 733, "ts": "04 Juil · 11h20", "model": "lstm-fr-v2.3"},
    {"id": 9018, "review_id": 108, "status": "erreur", "sentiment": "—", "confidence": 0.0, "latency": 3120, "ts": "04 Juil · 09h02", "model": "lstm-fr-v2.3"},
    {"id": 9017, "review_id": 107, "status": "succès", "sentiment": "negatif", "confidence": 0.88, "latency": 588, "ts": "03 Juil · 22h47", "model": "lstm-fr-v2.3"},
    {"id": 9016, "review_id": 106, "status": "succès", "sentiment": "positif", "confidence": 0.92, "latency": 470, "ts": "03 Juil · 20h15", "model": "lstm-fr-v2.3"},
    {"id": 9015, "review_id": 105, "status": "succès", "sentiment": "negatif", "confidence": 0.96, "latency": 655, "ts": "03 Juil · 18h33", "model": "lstm-fr-v2.3"},
]


def admin_users():
    return [
        {"id": 7, "name": "Yanice Mundele", "initials": "YM", "email": "yanice.client@canalbox.cd", "role": "client", "status": "actif", "reviews": 12, "joined": "12 Mar 2025"},
        {"id": 8, "name": "Joël Lumpungu", "initials": "JL", "email": "joel.stone@canalbox.cd", "role": "client", "status": "actif", "reviews": 8, "joined": "03 Avr 2025"},
        {"id": 9, "name": "Junior Bakana", "initials": "JB", "email": "junior.bakana@canalbox.cd", "role": "client", "status": "suspendu", "reviews": 3, "joined": "18 Avr 2025"},
        {"id": 1, "name": "David Débuze", "initials": "DD", "email": "david.admin@canalbox.cd", "role": "admin", "status": "actif", "reviews": 0, "joined": "05 Jan 2025"},
        {"id": 10, "name": "Grâce Kabongo", "initials": "GK", "email": "grace.kabongo@canalbox.cd", "role": "client", "status": "actif", "reviews": 21, "joined": "27 Fév 2025"},
        {"id": 11, "name": "Estelle Dyese", "initials": "ED", "email": "estelle.dyese@canalbox.cd", "role": "client", "status": "actif", "reviews": 5, "joined": "09 Mai 2025"},
    ]
