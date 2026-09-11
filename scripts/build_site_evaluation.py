"""Derive public evaluation data from canonical checked-in artifacts via unified builder."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_milestone_three_results import main as build_canonical_results


def main() -> None:
    build_canonical_results()


if __name__ == "__main__":
    main()
