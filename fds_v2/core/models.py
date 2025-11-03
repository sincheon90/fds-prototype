from typing import Optional, List
from pydantic import BaseModel, Field
from .enums import Decision, CaseKind

class EntityRefs(BaseModel):
    user: Optional[str] = None
    device: Optional[str] = None
    card: Optional[str] = None

class CaseParams(BaseModel):
    kind: CaseKind          # "order" | "purchase"
    case_id: str            # order_id or purchase_id
    refs: EntityRefs        # 햐 user/device/card references

class RegisterParams(BaseModel):
    user: Optional[str] = None
    device: Optional[str] = None
    card: Optional[str] = None

    def is_empty(self) -> bool:
        return not (self.user or self.device or self.card)

class Result(BaseModel):
    decision: Decision
    reasons: List[str] = Field(default_factory=list)
    register_blocklist: bool = False
    register_params: RegisterParams = Field(default_factory=RegisterParams)