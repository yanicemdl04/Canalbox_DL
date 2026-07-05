"""Ré-encode le vocabulaire TextVectorization en UTF-8 dans un fichier .keras."""

from __future__ import annotations

import shutil
import sys
import zipfile
from pathlib import Path


VOCAB_PATHS = (
    "assets/layers/text_vectorization/vocabulary.txt",
    "assets/layers/text_vectorization/_lookup_layer/vocabulary.txt",
)


def fix_vocabulary_bytes(raw: bytes) -> bytes:
    text = raw.decode("latin-1")
    return text.replace("\r\n", "\n").encode("utf-8")


def fix_keras_model(path: Path) -> None:
    backup = path.with_suffix(path.suffix + ".bak")
    if not backup.exists():
        shutil.copy2(path, backup)

    out_path = path.with_suffix(".keras.tmp")
    with zipfile.ZipFile(path, "r") as zin, zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename in VOCAB_PATHS:
                data = fix_vocabulary_bytes(data)
            zout.writestr(item, data)

    out_path.replace(path)
    print(f"OK — vocabulaire UTF-8 : {path}")
    if backup.exists():
        print(f"Sauvegarde : {backup}")


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "ml_models" / "lstm_sentiment_model.keras"
    fix_keras_model(target)
