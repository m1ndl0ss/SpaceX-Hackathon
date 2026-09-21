from __future__ import annotations

from impact_models.gbif import fetch_gbif
from impact_models.observations import save_fetch_status
from impact_models.roadkill import fetch_roadkill


def main() -> None:
    gbif_n, gbif_err = fetch_gbif()
    kill_n, kill_err = fetch_roadkill()
    save_fetch_status(
        {
            "gbif": gbif_n > 0,
            "roadkill": kill_n > 0,
            "gbifRecords": gbif_n,
            "roadkillRecords": kill_n,
            "gbifError": gbif_err,
            "roadkillError": kill_err,
        }
    )
    print(f"gbif={gbif_n} roadkill={kill_n}")
    if gbif_err:
        print(f"gbif warning: {gbif_err}")
    if kill_err:
        print(f"roadkill warning: {kill_err}")


if __name__ == "__main__":
    main()
