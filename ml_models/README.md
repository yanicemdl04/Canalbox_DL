jelly@jelly-HP-EliteBook-820-G3:/mnt/win-sda4/Users/Jelly/3D Objects/programmation/Python Project/Canalbox_DL$ ./run.sh 
./run.sh: ligne 9 : exec: python : non trouvé
jelly@jelly-HP-EliteBook-820-G3:/mnt/win-sda4/Users/Jelly/3D Objects/programmation/Python Project/Canalbox_DL$ 
# Canal Box — Modele de classification de sentiments (BiLSTM)

Documentation technique pour l'equipe **backend Django** : artefacts livres, architecture du modele, entrainement, evaluation et integration.

---

## 1. Objectif du modele

Analyser un **commentaire client Canal Box** (connexion, wifi, support, facturation…) et predire le **sentiment** :

| Classe     | Signification              | Index |
|------------|----------------------------|-------|
| `negative` | Insatisfaction, probleme   | 0     |
| `neutral`  | Avis mitige ou factuel     | 1     |
| `positive` | Satisfaction               | 2     |

**Entree** : texte brut (francais, parfois lingala / swahili / anglais melange).  
**Sortie** : classe predite + score de confiance + probabilites par classe.

---

## 2. Contenu du dossier `models/`

| Fichier | Role | Obligatoire |
|---------|------|-------------|
| `lstm_sentiment_model.keras` | Modele Keras complet (vectorizer + reseau) | **Oui** |
| `label_mapping.json` | Correspondance index → label | **Oui** |
| `inference.py` | Nettoyage texte + prediction (point d'entree backend) | **Oui** |
| `requirements.txt` | Dependances Python minimales | **Oui** |
| `vectorizer.pkl` | Copie du vocabulaire (debug / audit) | Non |
| `README.md` | Cette documentation | Recommande |

### Fichiers de nettoyage — ou est la logique ?

Le **nettoyage du texte** n'est **pas** dans le fichier `.keras`. Il est dans :

- **`models/inference.py`** → fonction `clean_text()` (version livree au backend)


**Regle importante** : le backend doit utiliser **exactement** la fonction `clean_text()` de `inference.py`. Toute difference (regex, casse, accents) peut changer la prediction.

```python
def clean_text(text: str) -> str:
    text = str(text).lower().strip()
    text = re.sub(r"[^a-zàâçéèêëîïôûùüÿñæœ0-9\s']", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
```

Actions effectuees : minuscules, suppression emojis/ponctuation, conservation des accents francais, espaces normalises.

---

## 3. Architecture du modele (pipeline complet)

Le fichier `.keras` contient un pipeline **Sequential** : une seule chaine de traitement de la phrase brute nettoyee jusqu'a la probabilite de sentiment.

```
Commentaire client (string)
        │
        ▼
┌───────────────────────┐
│  TextVectorization    │  Texte → sequence de 40 entiers (indices mots)
└───────────────────────┘
        │
        ▼
┌───────────────────────┐
│  Embedding (128 dim)  │  Chaque indice → vecteur dense appris
└───────────────────────┘
        │
        ▼
┌───────────────────────┐
│  Bidirectional LSTM   │  Lecture contexte gauche→droite ET droite→gauche
│  (64 unites, dropout) │
└───────────────────────┘
        │
        ▼
┌───────────────────────┐
│  Dropout (30 %)       │  Regularisation (desactive en inference)
└───────────────────────┘
        │
        ▼
┌───────────────────────┐
│  Dense (3 + softmax)  │  Probabilites : negative / neutral / positive
└───────────────────────┘
```

### 3.1 TextVectorization (vectorizer)

**Role** : convertir les mots en nombres, car un reseau de neurones ne lit pas le texte directement.

- Vocabulaire appris sur **1400 commentaires d'entrainement** (~3387 mots)
- `max_tokens` = 10 000
- Longueur fixe = **40 mots** (padding ou troncature)
- Mots inconnus → indice special (OOV)

Exemple : `"la connexion est lente"` → `[12, 845, 3, 1204, 0, 0, …, 0]`

Le vectorizer est **deja inclus** dans le `.keras` : pas besoin de `vectorizer.pkl` en production.

### 3.2 Embedding

**Role** : transformer chaque indice de mot en un **vecteur de 128 dimensions** qui capture des relations semantiques (ex. « lent » proche de « mauvais »).

- `input_dim` = taille du vocabulaire
- `output_dim` = 128
- `mask_zero=True` : ignore le padding (indices 0)

### 3.3 LSTM — rappel pedagogique

Un **LSTM** (Long Short-Term Memory) lit une phrase **mot par mot** et garde une **memoire** de ce qui a ete vu avant.

Pourquoi c'est utile en sentiment ?  
Le sens depend du **contexte** et de l'**ordre** des mots :

> « Le debit est **excellent** mais le support ne repond **jamais** »

Un modele qui ne lit que des mots isoles rate le « mais » et la fin negative. Le LSTM enchaine les mots et retient le contexte.

### 3.4 Pourquoi Bidirectional (BiLSTM) ?

Un LSTM simple lit de **gauche a droite** seulement. Un **BiLSTM** empile deux LSTM :

- un sens **gauche → droite**
- un sens **droite → gauche**

Les deux representations sont concatenees. Cela aide a capturer des tournures ou le sentiment est confirme ou infirme **a la fin** de la phrase (typique des avis Canal Box avec contradictions).

**Exemple Canal Box** : « Connexion correcte **sauf** le soir vers 21 h » — le BiLSTM exploite mieux la restriction en fin de phrase.

Parametres : 64 unites LSTM, `dropout=0.2`, `recurrent_dropout=0.2`.

### 3.5 Dropout + couche de sortie

- **Dropout 30 %** : utilise pendant l'entrainement pour limiter le surapprentissage (inactif en inference).
- **Dense(3, softmax)** : 3 neurones = 3 sentiments ; softmax → probabilites qui somment a 1.

---

## 4. Donnees et entrainement

| Element | Valeur |
|---------|--------|
| Dataset | 2000 commentaires synthetiques Canal Box |
| Colonnes | `text`, `rating`, `category`, `sentiment` |
| Repartition sentiments | ~667 negative / 666 neutral / 667 positive |
| Split | 70 % train (1400) / 15 % validation (300) / 15 % test (300) |
| Optimiseur | Adam |
| Loss | sparse_categorical_crossentropy |
| Metrique | accuracy |
| Batch size | 32 |
| Epochs max | 30 |
| Early stopping | patience 3 sur `val_loss` |
| Checkpoint | meilleur modele sur `val_loss` |

Notebook de reference : `notebooks/01_train_lstm_sentiment.ipynb`

---

## 5. Evaluation (jeu de test — 300 avis jamais vus)

| Metrique | Valeur |
|----------|--------|
| **Accuracy test** | **72,33 %** |
| Support par classe | 100 avis chacun |

| Classe   | Precision | Recall | F1-score |
|----------|-----------|--------|----------|
| negatif  | 0,76      | 0,68   | 0,72     |
| neutre   | 0,67      | 0,78   | 0,72     |
| positif  | 0,76      | 0,71   | 0,73     |

Rapport detaille : `reports/classification_report.txt`  
Matrice de confusion : `reports/confusion_matrix.png`  
Courbes d'entrainement : `reports/training_curves.png`

**Limites connues** : modele entraine sur donnees synthetiques ; performances reelles peuvent varier sur de vrais tickets clients. La classe `neutral` reste la plus ambigue.

---

## 6. Installation des dependances

### Environnement dedie (recommande)

```bash
cd models
python -m venv venv
# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

### Versions testees a l'export

| Composant | Version |
|-----------|---------|
| Python | 3.12.x |
| TensorFlow | 2.21.0 |

### Points d'attention versions

1. **TensorFlow** : utiliser une version **2.15 à 2.21**. Eviter de charger le `.keras` avec TensorFlow 2.10 ou inferieur.
2. **Python** : 3.10, 3.11 ou 3.12 recommande. Eviter 3.13+ tant que TensorFlow ne le supporte pas officiellement.
3. **GPU** : sous Windows natif, TensorFlow >= 2.11 n'utilise **pas** le GPU ; l'inference CPU suffit pour un flux modere de commentaires.
4. **Ne pas modifier** `label_mapping.json` sans reentrainer le modele : les indices doivent correspondre a la couche softmax.
5. **Warnings au demarrage** (`oneDNN`, `GPU not available`) : messages informatifs, pas des erreurs. `inference.py` les reduit via `TF_CPP_MIN_LOG_LEVEL=2`.

### Performance et temps de reponse

| Contexte | Temps typique | Explication |
|----------|---------------|-------------|
| **CLI** `python inference.py --text "..."` | **10–50 s** | Chaque commande relance Python + import TensorFlow + chargement `.keras` |
| **Django** (modele pre-charge au startup) | **100–500 ms** | TensorFlow et le modele restent en memoire |
| **2e prediction** (meme processus Python) | ~100 ms | Seule l'inference est relancee |

Detail du temps en CLI (champ `timing_ms` dans la reponse JSON) :

| Etape | Duree typique |
|-------|---------------|
| `tensorflow_import` | 15–25 s |
| `model_load` | 1–2 s |
| `predict` (1er appel) | 3–5 s |
| `clean_text` | < 1 ms |

**Important** : un test CLI lent **ne signifie pas** que l'API Django sera lente. En production, appeler `load_model()` une fois dans `AppConfig.ready()`.

**Eviter** l'option sous-processus (Option B Django) en production : elle relance TensorFlow a chaque requete.

Copier le projet hors de **OneDrive** peut accelerer le chargement du fichier `.keras` (~6 Mo).

---

## 7. Tester le modele (avant integration Django)

### Test rapide en ligne de commande

Depuis la racine du projet :

```bash
python models/inference.py --text "La connexion est rapide et stable."
```

Avec progression affichee pendant le chargement (recommande pour comprendre les delais) :

```bash
python models/inference.py --text "Le service coupe tous les soirs !" --verbose
```

Le flag `--verbose` ecrit sur **stderr** (`Initialisation TensorFlow...`, `Chargement du modele Keras...`). La reponse JSON reste sur stdout.

Reponse attendue (JSON) :

```json
{
  "text_clean": "la connexion est rapide et stable",
  "sentiment": "positive",
  "confidence": 0.8574,
  "probabilities": {
    "negative": 0.0781,
    "neutral": 0.0645,
    "positive": 0.8574
  },
  "processing_time_ms": 13080.63,
  "timing_ms": {
    "tensorflow_import": 8200.0,
    "model_load": 1100.0,
    "predict": 3700.0,
    "clean_text": 0.5,
    "total": 13080.63
  }
}
```

`processing_time_ms` = `timing_ms.total`. En CLI, la majorite du temps est l'import TensorFlow, pas la prediction elle-meme.

### Test en Python interactif

```python
from pathlib import Path
import sys
sys.path.insert(0, str(Path("models").resolve().parent))

from models.inference import predict_sentiment, clean_text, load_model

load_model()  # pre-charge une seule fois
print(clean_text("Top !!! 😊"))
print(predict_sentiment("Le debit est bon mais le support est lent."))
print(predict_sentiment("Encore un test"))  # beaucoup plus rapide
```

### Valider que tous les artefacts sont presents

Depuis la racine du projet :

```bash
python src/export_model.py
```

---

## 8. Integration Django

### Option A — Import direct (meme processus Python) **recommandee**

Copier le dossier `models/` dans le projet Django (ou le referencer via un sous-module).

```python
# canalbox_ai/services/sentiment.py
from models.inference import predict_sentiment

def analyze_comment(text: str) -> dict:
    return predict_sentiment(text)
```

```python
# views.py
from django.http import JsonResponse
from .services.sentiment import analyze_comment

def sentiment_api(request):
    text = request.POST.get("text", "")
    if not text.strip():
        return JsonResponse({"error": "text requis"}, status=400)
    return JsonResponse(analyze_comment(text))
```

**Charger le modele une seule fois au demarrage** (evite 15–25 s par requete) :

```python
# apps.py
from django.apps import AppConfig

class SentimentConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sentiment"

    def ready(self):
        from models.inference import load_model, predict_sentiment

        load_model()
        # Warmup : 1ere inference compile le graphe TensorFlow
        predict_sentiment("warmup", verbose=False)
```

Enregistrer l'app dans `INSTALLED_APPS` et s'assurer que `ready()` n'est execute qu'une fois (pas en mode `runserver` reload double — comportement Django connu ; acceptable en dev).

### Option B — Sous-processus

Si Django et le modele sont dans des venv separes :

```python
import json
import subprocess

def predict_via_cli(text: str) -> dict:
    result = subprocess.run(
        ["python", "models/inference.py", "--text", text],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)
```

Moins performant : **relance TensorFlow a chaque requete** (10–50 s). Reserve au prototypage uniquement.

### Option C — Microservice REST

Exposer `inference.py` via FastAPI/Flask ; Django appelle HTTP. Utile si l'equipe ML et backend sont decouplees.

### Checklist integration Django

- [ ] Dossier `models/` complet copie dans le depot backend
- [ ] `pip install -r models/requirements.txt` dans le venv Django (ou venv dedie)
- [ ] Test CLI OK avant branchement API
- [ ] `load_model()` au demarrage de l'app
- [ ] Endpoint renvoie `sentiment`, `confidence`, `probabilities`
- [ ] Gestion erreur si texte vide ou modele absent
- [ ] Ne pas reimplementer `clean_text` a la main — utiliser `inference.py`
- [ ] Prevoir timeout / file d'attente si volume eleve (inference CPU)

---

## 9. Format de reponse API suggere

```json
{
  "text_clean": "le wifi coupe tout le temps",
  "sentiment": "negative",
  "confidence": 0.91,
  "probabilities": {
    "negative": 0.91,
    "neutral": 0.05,
    "positive": 0.04
  },
  "processing_time_ms": 180.5,
  "timing_ms": {
    "tensorflow_import": 0.0,
    "model_load": 0.0,
    "predict": 175.0,
    "clean_text": 0.3,
    "total": 180.5
  }
}
```

En API Django pre-chargee, `tensorflow_import` et `model_load` sont proches de **0** (deja en memoire).

Mapping des labels affichage (optionnel cote frontend) :

| `sentiment` | Affichage FR |
|-------------|--------------|
| `negative`  | Negatif      |
| `neutral`   | Neutre       |
| `positive`  | Positif      |

---

## 10. Depannage

| Probleme | Cause probable | Solution |
|----------|----------------|----------|
| `FileNotFoundError: lstm_sentiment_model.keras` | Chemin incorrect | Garder `inference.py` et `.keras` dans le meme dossier |
| Prediction incoherente | Nettoyage different | Utiliser `clean_text()` de `inference.py` |
| CLI tres lente (10–50 s) | Cold start normal | Utiliser `--verbose` pour voir `timing_ms` ; pre-charger en Django |
| API Django lente | Modele non pre-charge | `load_model()` + warmup dans `AppConfig.ready()` |
| Warnings `oneDNN` / `GPU` | Informatifs TensorFlow | Ignorer ou variables env deja dans `inference.py` |
| Erreur chargement `.keras` | Version TensorFlow | Installer TensorFlow 2.15–2.21 |
| `ModuleNotFoundError: tensorflow` | venv incomplet | `pip install -r models/requirements.txt` |

---

## 11. Contact / evolution

- Reentrainer ou mettre a jour le modele : notebook `notebooks/01_train_lstm_sentiment.ipynb`
- Nouvelle version du `.keras` → redeployer tout le dossier `models/` + retester `inference.py`
- Toute modification de `clean_text` ou du vocabulaire necessite un **reexport complet** du modele

---

*Canal Box — Projet Deep Learning L4 FASI — Classification de sentiments BiLSTM*
