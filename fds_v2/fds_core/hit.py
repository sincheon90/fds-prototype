from dataclasses import dataclass
from .enums import Decision
from enum import IntFlag, auto

class RegisterTarget(IntFlag):
    """Bitmask for what to register into blocklist."""
    NONE   = 0
    USER   = auto()
    DEVICE = auto()
    CARD   = auto()
    ALL    = USER | DEVICE | CARD

@dataclass
class Hit:
    rule_id: str
    decision : Decision
    reason: str = ""
    register_target: RegisterTarget = RegisterTarget.NONE
    register_blocklist: bool = False