from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field
import hashlib
import json
import time


class RuleType(str, Enum):
    required_field = "required_field"
    conditional_required_field = "conditional_required_field"
    date_validation = "date_validation"
    numeric_comparison = "numeric_comparison"
    amount_calculation = "amount_calculation"
    currency_consistency = "currency_consistency"
    tax_category_validation = "tax_category_validation"
    duplicate_field_check = "duplicate_field_check"


class Severity(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RuleIR(BaseModel):
    rule_id: str
    rule_text: str

    # Core rule fields
    rule_type: RuleType
    severity: Severity = Severity.HIGH

    # XPath target
    field_xpath: str

    # Optional rule conditions
    condition_xpath: Optional[str] = None
    expected_value: Optional[Any] = None
    operator: Optional[str] = None

    # User-facing validation message
    expected_error_message: str

    # Metadata
    content_hash: str = Field(default="")
    created_at: float = Field(default_factory=time.time)
    version: int = 1

    def model_post_init(self, __context: Any) -> None:
        """
        Generate deterministic content hash
        for audit/version tracking.
        """

        if not self.content_hash:
            payload = {
                "rule_type": str(self.rule_type),
                "field_xpath": self.field_xpath,
                "condition_xpath": self.condition_xpath,
                "expected_value": self.expected_value,
                "operator": self.operator,
            }

            self.content_hash = hashlib.sha256(
                json.dumps(payload, sort_keys=True).encode()
            ).hexdigest()[:16]


class ValidationResult(BaseModel):
    rule_id: str

    # PASS / FAIL
    passed: bool

    # Validation details
    xpath_location: Optional[str] = None
    expected: Optional[Any] = None
    actual: Optional[Any] = None

    # Human-readable message
    message: str

    # Severity level
    severity: Severity = Severity.HIGH