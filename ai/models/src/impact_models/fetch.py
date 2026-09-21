from __future__ import annotations

from impact_models.gbif import fetch_gbif
from impact_models.observations import save_fetch_status
from impact_models.roadkill import fetch_roadkill
from impact_models.warehouse import warehouse_flags


def main() -> None:
    flags = warehouse_flags()
    gbif_n, gbif_err = 0, None
    kill_n, kill_err = 0, None
    if flags.get("gbif"):
        print("gbif: using collector warehouse, skip live fetch")
    else:
        gbif_n, gbif_err = fetch_gbif()
    if flags.get("roadkill"):
        print("roadkill: using collector warehouse, skip live fetch")
    else:
        kill_n, kill_err = fetch_roadkill()
    save_fetch_status(
        {
            **flags,
            "gbif": bool(flags.get("gbif") or gbif_n > 0),
            "roadkill": bool(flags.get("roadkill") or kill_n > 0),
            "gbifRecords": gbif_n,
            "roadkillRecords": kill_n,
            "gbifError": gbif_err,
            "roadkillError": kill_err,
        }
    )
    print(f"gbif={gbif_n} roadkill={kill_n} warehouse={flags}")
    if gbif_err:
        print(f"gbif warning: {gbif_err}")
    if kill_err:
        print(f"roadkill warning: {kill_err}")


if __name__ == "__main__":
    main()
