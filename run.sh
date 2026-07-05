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
  echo "Créez le venv : uv venv .venv --python 3.12 && uv pip install -r requirements.txt"
  exit 1
fi

exec "$PY" manage.py runserver "${1:-8888}"
