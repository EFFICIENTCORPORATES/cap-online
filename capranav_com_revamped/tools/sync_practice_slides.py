"""Copy canonical Practice with Pranav Bhaiya HTML decks into Worker Assets."""

from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "books/ca-inter/smat-may-27-edition/practice-with-pranav-bhaiya/slides"
DESTINATION = ROOT / "capranav_com_revamped/public/practice-with-pranav-bhaiya/slides"
DECKS = (
    "day-01-opening.html",
    "day-01-syllabus-flow.html",
    "day-01-marks-split.html",
)


def main():
    DESTINATION.mkdir(parents=True, exist_ok=True)
    for name in DECKS:
        source = SOURCE / name
        if not source.is_file():
            raise FileNotFoundError(f"Missing canonical slide deck: {source}")
        shutil.copy2(source, DESTINATION / name)
        print(f"Synced {name}")


if __name__ == "__main__":
    main()
