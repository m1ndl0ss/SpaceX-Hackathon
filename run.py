"""Collect Benelux caches. Scoring is stale and opt-in only."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from collectors.run_collectors import main as collect


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--score-only', action='store_true', help='run stale Abruzzo scoring (not the Benelux baseline)')
    p.add_argument('--collect-only', action='store_true', help='collect caches and exit (default behaviour)')
    args = p.parse_args()
    if args.score_only:
        from scoring.engine import score_all
        print('scoring engine is stale (Abruzzo bear composite); not a Benelux baseline')
        result = score_all()
        print(f"scored {result['cell_count']} cells")
        return
    collect()
    print('collection cached under data/*_latest.json')


if __name__ == '__main__':
    main()
