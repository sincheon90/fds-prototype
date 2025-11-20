from enum import Enum

class Decision(str, Enum):
    # severity: BLOCK, REVIEW, ALLOW
    BLOCK = "block"
    REVIEW = "review"
    ALLOW = "allow"

class CaseKind(str, Enum):
    ORDER = "order"
    PURCHASE = "purchase"