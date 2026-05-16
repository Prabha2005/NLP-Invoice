import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.models.ir import RuleIR, RuleType, Severity


def test_content_hash_generated():
    rule = RuleIR(
        rule_id="r001",
        rule_text="Invoice must have a DueDate.",
        rule_type=RuleType.required_field,
        severity=Severity.HIGH,
        field_xpath="//cbc:DueDate",
        expected_error_message="DueDate is required.",
    )
    assert len(rule.content_hash) == 16


def test_same_rule_same_hash():
    kwargs = dict(
        rule_id="r001",
        rule_text="Invoice must have a DueDate.",
        rule_type=RuleType.required_field,
        severity=Severity.HIGH,
        field_xpath="//cbc:DueDate",
        expected_error_message="DueDate is required.",
    )
    r1 = RuleIR(**kwargs)
    r2 = RuleIR(**{**kwargs, "rule_id": "r002"})
    assert r1.content_hash == r2.content_hash


def test_compiler_produces_xslt():
    from app.compiler.xslt_compiler import compile_to_xslt
    rule = RuleIR(
        rule_id="r001",
        rule_text="Invoice must have a DueDate.",
        rule_type=RuleType.required_field,
        severity=Severity.HIGH,
        field_xpath="//cbc:DueDate",
        expected_error_message="DueDate is required.",
    )
    xslt = compile_to_xslt(rule)
    assert "xsl:stylesheet" in xslt
    assert "DueDate" in xslt
    assert rule.content_hash in xslt
