from __future__ import annotations
from lxml import etree
from app.models.ir import RuleIR, ValidationResult, Severity
from app.compiler.xslt_compiler import compile_to_xslt


def validate(rule: RuleIR, invoice_xml: str) -> list[ValidationResult]:
    xslt_src = compile_to_xslt(rule)
    xslt_tree = etree.fromstring(xslt_src.encode())
    transform = etree.XSLT(xslt_tree)
    invoice_tree = etree.fromstring(invoice_xml.encode())
    result_tree = transform(invoice_tree)

    results: list[ValidationResult] = []
    for node in result_tree.getroot():
        tag = node.tag
        if tag == "pass":
            results.append(ValidationResult(
                rule_id=node.get("rule-id", rule.rule_id),
                passed=True,
                message="OK",
                severity=rule.severity,
            ))
        elif tag == "failure":
            results.append(ValidationResult(
                rule_id=node.get("rule-id", rule.rule_id),
                passed=False,
                xpath_location=node.get("xpath"),
                expected=_text(node, "expected"),
                actual=_text(node, "actual"),
                message=_text(node, "message") or rule.expected_error_message,
                severity=Severity(node.get("severity", rule.severity)),
            ))
    return results


def _text(node: etree._Element, tag: str) -> str | None:
    child = node.find(tag)
    return child.text if child is not None else None
