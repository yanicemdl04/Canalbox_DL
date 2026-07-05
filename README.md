# Canal Box — Plateforme d'avis clients avec analyse LSTM

Application web **monolithique Django** pour la collecte d'avis clients **Canal Box**
(internet, TV, SAV, facturation) avec **analyse de sentiments** par réseau LSTM intégrée
au backend. Design *Liquid Glass*, animations GSAP, contrôle d'accès strict par rôle.

> Projet académique — Examen Deep Learning (thème LSTM) · Cahier des charges v1.1

## Stack technique

| Couche | Technologies |
|--------|-------------|
| **Backend** | Django 5.2, ORM, SQLite |
| **Frontend** | Django Templates, HTML5, Tailwind CSS (CDN), GSAP |
| **IA** | Stub LSTM (`core/ml/`) — prêt pour modèle Keras `.h5` |
| **Auth** | Django Auth (e-mail + mot de passe), rôles client / admin |
| **Design** | Liquid Glass, Lucide SVG, Inter / Manrope |

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate           # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_canalbox       # données initiales
python manage.py runserver
```

Ouvrez **http://127.0.0.1:8000/**

## Comptes de démonstration

| Rôle | E-mail | Mot de passe |
|------|--------|--------------|
| **Client** | `yanice.client@canalbox.cd` | `demo1234` |
| **Administrateur** | `david.admin@canalbox.cd` | `demo1234` |

Accès rapide : `/connexion/?demo=client` ou `/connexion/?demo=admin`

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Application Django monolithique             │
├──────────────┬──────────────────────┬───────────────────┤
│  Templates   │   Vues + Services    │   SQLite (ORM)    │
│  public/     │   views.py           │   User            │
│  client/     │   review_service     │   Category        │
│  adminpanel/ │   stats_service      │   Review          │
│              │   ml/lstm_service    │   SentimentResult │
│              │                      │   InferenceLog    │
└──────────────┴──────────────────────┴───────────────────┘
                         │
              ┌──────────▼──────────┐
              │  Moteur LSTM (stub)  │
              │  → lstm_keras (.h5)  │
              └─────────────────────┘
```

### Flux — soumission d'un avis

1. Le client remplit le formulaire (titre, texte, note, catégorie).
2. Le backend enregistre l'avis (`status: pending`).
3. Le service LSTM analyse le texte et stocke sentiment + confiance.
4. L'avis passe en `analyzed` — le client ne voit **aucune** donnée IA.
5. L'administrateur consulte sentiment, confiance, logs et statistiques.

## Structure du projet

```
canalbox/                  Configuration Django (settings, urls)
core/
  models.py                Modèles ORM (User, Review, Sentiment…)
  views.py                 Vues + contrôle d'accès par rôle
  presenters.py            Conversion ORM → templates
  urls.py                  Routes HTTP
  admin.py                 Interface Django Admin
  services/
    review_service.py      Création avis + inférence LSTM
    stats_service.py       Statistiques dashboard admin
  ml/
    lstm_service.py        Interface d'inférence
    lstm_stub.py           Stub heuristique (actif)
    lstm_keras.py          Branche modèle réel (à venir)
  management/commands/
    seed_canalbox.py       Jeu de données initial
ml_models/                 Emplacement du modèle .h5
templates/
  public/                  Landing, connexion, inscription
  client/                  Espace client
  adminpanel/              Console administrateur
  partials/                Composants réutilisables
static/
  css/canalbox.css         Design system Liquid Glass
  js/canalbox.js           Animations GSAP
docs/
  CanalBox_Documentation.pdf   Documentation illustrée du projet
scripts/
  generate_project_pdf.py  Régénérer le PDF de documentation
```

## Modèle de données

| Table | Champs clés |
|-------|-------------|
| `users` | email, role, plan, status, password |
| `categories` | name, slug, description, icon |
| `reviews` | user_id, title, content, rating, category_id, status, flagged |
| `sentiment_results` | review_id, sentiment, confidence, prob_*, processing_ms |
| `inference_logs` | review_id, status, latency_ms, model_version |

## Règle de rôle (cahier des charges)

Les données IA (**sentiment, confiance, logs, statistiques LSTM**) ne sont transmises
**qu'aux templates administrateur**. Les vues client utilisent `review_to_dict(include_ia=False)`.

## Pages disponibles

### Public
| URL | Page |
|-----|------|
| `/` | Landing |
| `/connexion/` | Connexion |
| `/inscription/` | Inscription |
| `/mot-de-passe-oublie/` | Mot de passe oublié |

### Espace client
| URL | Page |
|-----|------|
| `/espace/` | Tableau de bord |
| `/espace/avis/` | Liste des avis (filtres, pagination) |
| `/espace/avis/nouveau/` | Rédiger un avis |
| `/espace/avis/<id>/` | Détail d'un avis |
| `/espace/profil/` | Profil |
| `/espace/profil/modifier/` | Modifier le profil |

### Console administrateur
| URL | Page |
|-----|------|
| `/administration/` | Tableau de bord analytique |
| `/administration/avis/` | Avis avec sentiment LSTM |
| `/administration/avis/<id>/` | Détail + distribution softmax |
| `/administration/moderation/` | Avis signalés |
| `/administration/utilisateurs/` | Gestion des comptes |
| `/administration/categories/` | Catégories de services |
| `/administration/logs/` | Logs d'inférence LSTM |
| `/administration/exports/csv/` | Export CSV |
| `/administration/exports/pdf/` | Export PDF |

## Intégration du modèle LSTM

1. Placer le fichier entraîné dans `ml_models/lstm_sentiment.h5`
2. Implémenter `predict()` dans `core/ml/lstm_keras.py`
3. Modifier `canalbox/settings.py` :

```python
LSTM_BACKEND = 'keras'
LSTM_MODEL_VERSION = 'lstm-fr-v2.3'
```

## Commandes utiles

```bash
python manage.py seed_canalbox --flush   # réinitialiser les données
python manage.py generate_project_pdf    # régénérer la documentation PDF
python manage.py createsuperuser         # accès /django-admin/
```

## Documentation PDF

Un document illustré et coloré est disponible dans `docs/CanalBox_Documentation.pdf`.
Régénérez-le avec :

```bash
python manage.py generate_project_pdf
```

## Palette Canal Box

Blanc & noir dominants, **rose Canal Box** (`#ff2d78`) pour les actions.
Sentiments : vert `#12b76a` (positif), rouge `#f04438` (négatif), ambre `#f79009` (neutre).
