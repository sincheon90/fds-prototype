from typing import Any, List

from fds_v2.core.hit import Hit


def register_blocklist(kind: str, ref_id: Any, hits: List[Hit]) -> None: ...