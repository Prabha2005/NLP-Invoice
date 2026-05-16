from __future__ import annotations
import json, uuid
from app.models.ir import RuleIR

try:
    import ollama
    _OLLAMA_AVAILABLE = True
except ImportError:
    _OLLAMA_AVAILABLE = False

_SYSTEM_PROMPT = """
You are a rule parser for XML invoice validation. Given a plain-English rule, return ONLY a valid JSON object with these exact keys:

{
  "rule_type": one of [required_field, conditional_required_field, date_validation, numeric_comparison, amount_calculation, currency_consistency, tax_category_validation, duplicate_field_check],
  "severity": one of [HIGH, MEDIUM, LOW],
  "field_xpath": "XPath expression targeting the field in a UBL 2.1 invoice namespace",
  "condition_xpath": "XPath condition string or null",
  "expected_value": "expected value or null",
  "operator": one of [eq, ne, lt, gt, lte, gte, matches, exists] or null,
  "expected_error_message": "short human-readable error message"
}

UBL 2.1 namespace prefixes:
  cbc = urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2
  cac = urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2

Return ONLY the JSON object. No explanation, no markdown, no code fences.
""".strip()


def parse_rule(rule_text: str, rule_id: str | None = None) -> RuleIR:
    if not _OLLAMA_AVAILABLE:
        raise RuntimeError("ollama package not installed. Run: pip install ollama")

    response = ollama.chat(
        model="llama3.2",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": rule_text},
        ],
        format="json",
    )

    raw = response["message"]["content"]
    data = json.loads(raw)
    data["rule_id"] = rule_id or str(uuid.uuid4())[:8]
    data["rule_text"] = rule_text

    return RuleIR(**data)
