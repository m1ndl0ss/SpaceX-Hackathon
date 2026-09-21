"""Collect (or reuse cache) then score. Use --score-only on stage."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from collectors.run_collectors import main as collect
from scoring.engine import score_all


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--score-only', action='store_true')
    args = p.parse_args()
    if not args.score_only:
        collect()
    result = score_all()
    print(f"scored {result['cell_count']} cells")
    print('cached data/scores/cells_latest.json and data/cache/frontend_latest.json')
    if result['cells']:
        top = result['cells'][0]
        print(f"top cell {top['cell_id']} composite={top['composite']}")


if __name__ == '__main__':
    main()
