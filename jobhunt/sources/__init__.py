"""Job sources. Each module exposes tasks(cfg) -> (label, callable(get) -> list[Job])."""
from jobhunt.sources import boards, feeds


def all_tasks(cfg: dict, only: set[str] | None = None):
    """Every enabled source task. `only` filters by the part before the colon."""
    for mod in (boards, feeds):
        for label, fn in mod.tasks(cfg):
            if only and label.split(":")[0] not in only:
                continue
            yield label, fn
