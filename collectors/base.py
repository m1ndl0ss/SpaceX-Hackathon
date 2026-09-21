import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def with_retry(fn, delays=None):
    if delays is None:
        delays = [1, 2, 4]
    last_err = None
    for i, delay in enumerate([0] + delays):
        if delay:
            time.sleep(delay)
        try:
            return fn()
        except Exception as e:
            last_err = e
            print(f'  retry {i}/{len(delays)}: {e}')
    raise last_err


@dataclass
class CollectedRecord:
    source_id: str
    source_name: str
    source_url: str
    collected_at: str
    raw: dict
    license: str = ''
    geometry: dict | None = None

    def to_dict(self):
        return asdict(self)
