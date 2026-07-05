#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

PY=""
for candidate in .venv/bin/python .venv/bin/python3 .venv-ml/bin/python .venv-ml/bin/python3; do
  if [[ -x "$candidate" ]]; then
    PY="$candidate"
    break
  fi
done

if [[ -z "$PY" ]]; then
  echo "Erreur : aucun Python de venv trouvé."
  echo "Créez le venv : uv venv .venv --python 3.12 && uv pip install -r requirements.txt --python .venv/bin/python"
  exit 1
fi

if ! "$PY" -c "import whitenoise" 2>/dev/null; then
  echo "Installation des dépendances manquantes..."
  if command -v uv >/dev/null; then
    uv pip install -r requirements.txt --python "$PY"
  else
    echo "Erreur : whitenoise absent. Lancez : uv pip install -r requirements.txt --python $PY"
    exit 1
  fi
fi

exec "$PY" manage.py runserver "${1:-8888}"
