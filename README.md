# Canal Box — Interface (Frontend Django)

Interface web **premium** pour la plateforme d'avis clients **Canal Box** avec analyse
de sentiments par réseau **LSTM**. Design *Liquid Glass* (Apple / iOS 26 / visionOS),
animations **GSAP**, respect strict des rôles utilisateur.

> Projet académique — Examen Deep Learning (thème LSTM). Cette partie couvre
> **uniquement le frontend**. Le backend réel (API REST, modèle LSTM, JWT, Supabase)
> est défini par ailleurs ; les vues Django incluses ici simulent ce backend avec des
> **données de démonstration** afin de rendre l'interface entièrement navigable.

## Stack technique

- **Django Templates** (Django 5.2)
- **HTML5 / CSS3**
- **Tailwind CSS** (Play CDN)
- **JavaScript ES6+**
- **GSAP** + ScrollTrigger (animations)
- Icônes **Lucide** (sprite SVG unifié)
- Typographie **Inter / Manrope**

## Palette Canal Box

Blanc & noir dominants, **rose Canal Box** (`#ff2d78`) réservé aux actions et éléments
interactifs importants. Déclinaisons de gris pour la profondeur.

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Ouvrez http://127.0.0.1:8000/

## Comptes de démonstration

Sur la page de connexion, deux boutons permettent de choisir le rôle :

| Rôle          | Accès |
|---------------|-------|
| **Client**    | Dashboard, avis, recherche/filtres, profil — **aucune donnée IA** |
| **Administrateur** | Tableau de bord analytique, sentiment & score LSTM, modération, logs, exports |

## Structure

```
canalbox/            Configuration du projet Django
core/                Application principale (vues, urls, données de démo, filtres)
  demo_data.py       Jeux de données simulant le backend
  views.py           Vues + contrôle d'accès par rôle (simulation)
  templatetags/      Filtres de template (étoiles, sentiment…)
templates/
  base*.html         Layouts (public / client / admin)
  partials/          Composants réutilisables (navbar, sidebar, icônes, cartes…)
  public/            Landing, connexion, inscription, mot de passe oublié
  client/            Espace client
  adminpanel/        Console administrateur
static/
  css/canalbox.css   Design system Liquid Glass
  js/canalbox.js     Animations GSAP & interactions
```

## Règle de rôle (cahier des charges)

Les informations d'analyse (**sentiment, score de confiance, statistiques IA**) ne sont
transmises **qu'aux templates de l'espace administrateur**. Les vues client filtrent
explicitement ces champs (`_client_review`). Les clients ne voient jamais ces données.

## Pages disponibles

**Public** : Landing · Connexion · Inscription · Mot de passe oublié
**Client** : Tableau de bord · Liste des avis · Recherche & filtres · Détail d'un avis ·
Écrire un avis · Profil · Modifier le profil
**Admin** : Tableau de bord analytique · Avis analysés (sentiment + confiance) ·
Détail LSTM · Modération · Utilisateurs · Catégories · Logs d'inférence · Exports CSV/PDF
