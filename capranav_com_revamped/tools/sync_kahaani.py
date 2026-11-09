"""Copy the canonical Kahaani decks into Worker Assets (public/kahaani/).

Canonical sources live under content/productions/<slug>/deck/ and are generated there (see that folder's README).
Run this BEFORE tools/apply_seo_meta.py (which adds the head block to the copy) and tools/apply_legal_notice.py.
"""

from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
DESTINATION = ROOT / "capranav_com_revamped/public/kahaani"
DECKS = (
    # (canonical source, published file name)
    ("content/productions/restructuring-lecture-1/deck/kahaani-restructuring-map.html",
     "reconstruction-amalgamation-consolidation.html"),
)


def main():
    DESTINATION.mkdir(parents=True, exist_ok=True)
    for source, name in DECKS:
        src = ROOT / source
        if not src.is_file():
            raise FileNotFoundError(f"Missing canonical Kahaani deck: {src}")
        shutil.copy2(src, DESTINATION / name)
        print(f"Synced {name}")


if __name__ == "__main__":
    main()
