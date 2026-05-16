from __future__ import annotations
from app.models.ir import RuleIR, RuleType

_NS = (
    'xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2" '
    'xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2" '
    'xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"'
)

_XSLT_WRAPPER = """\
<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
  xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
  xmlns:xs="http://www.w3.org/2001/XMLSchema">

  <xsl:output method="xml" indent="yes"/>

  <xsl:template match="/">
    <validation-results rule-id="{rule_id}" content-hash="{content_hash}">
{assertions}
    </validation-results>
  </xsl:template>

</xsl:stylesheet>"""


def _required_field(rule: RuleIR) -> str:
    return f"""\
      <xsl:variable name="field" select="{rule.field_xpath}"/>
      <xsl:choose>
        <xsl:when test="not($field) or $field = ''">
          <failure rule-id="{rule.rule_id}" severity="{rule.severity}" xpath="{rule.field_xpath}">
            <message>{rule.expected_error_message}</message>
          </failure>
        </xsl:when>
        <xsl:otherwise><pass rule-id="{rule.rule_id}"/></xsl:otherwise>
      </xsl:choose>"""


def _conditional_required(rule: RuleIR) -> str:
    condition = rule.condition_xpath or "true()"
    return f"""\
      <xsl:if test="{condition}">
        <xsl:variable name="field" select="{rule.field_xpath}"/>
        <xsl:choose>
          <xsl:when test="not($field) or $field = ''">
            <failure rule-id="{rule.rule_id}" severity="{rule.severity}" xpath="{rule.field_xpath}">
              <message>{rule.expected_error_message}</message>
            </failure>
          </xsl:when>
          <xsl:otherwise><pass rule-id="{rule.rule_id}"/></xsl:otherwise>
        </xsl:choose>
      </xsl:if>"""


def _numeric_comparison(rule: RuleIR) -> str:
    op_map = {"eq": "=", "ne": "!=", "lt": "<", "gt": ">", "lte": "<=", "gte": ">="}
    op = op_map.get(rule.operator or "eq", "=")
    expected = rule.expected_value or 0
    return f"""\
      <xsl:variable name="val" select="number({rule.field_xpath})"/>
      <xsl:choose>
        <xsl:when test="not($val {op} {expected})">
          <failure rule-id="{rule.rule_id}" severity="{rule.severity}" xpath="{rule.field_xpath}">
            <expected>{expected}</expected>
            <actual><xsl:value-of select="$val"/></actual>
            <message>{rule.expected_error_message}</message>
          </failure>
        </xsl:when>
        <xsl:otherwise><pass rule-id="{rule.rule_id}"/></xsl:otherwise>
      </xsl:choose>"""


def _date_validation(rule: RuleIR) -> str:
    return f"""\
      <xsl:variable name="d" select="{rule.field_xpath}"/>
      <xsl:choose>
        <xsl:when test="not($d) or not(matches($d, '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}$'))">
          <failure rule-id="{rule.rule_id}" severity="{rule.severity}" xpath="{rule.field_xpath}">
            <actual><xsl:value-of select="$d"/></actual>
            <message>{rule.expected_error_message}</message>
          </failure>
        </xsl:when>
        <xsl:otherwise><pass rule-id="{rule.rule_id}"/></xsl:otherwise>
      </xsl:choose>"""


def _amount_calculation(rule: RuleIR) -> str:
    condition = rule.condition_xpath or "true()"
    return f"""\
      <xsl:choose>
        <xsl:when test="not({condition})">
          <failure rule-id="{rule.rule_id}" severity="{rule.severity}">
            <message>{rule.expected_error_message}</message>
          </failure>
        </xsl:when>
        <xsl:otherwise><pass rule-id="{rule.rule_id}"/></xsl:otherwise>
      </xsl:choose>"""


def _currency_consistency(rule: RuleIR) -> str:
    return f"""\
      <xsl:variable name="base" select="{rule.field_xpath}"/>
      <xsl:for-each select="//*[@currencyID and @currencyID != $base]">
        <failure rule-id="{rule.rule_id}" severity="{rule.severity}">
          <expected><xsl:value-of select="$base"/></expected>
          <actual><xsl:value-of select="@currencyID"/></actual>
          <message>{rule.expected_error_message}</message>
        </failure>
      </xsl:for-each>"""


def _fallback(rule: RuleIR) -> str:
    return _required_field(rule)


_BUILDERS = {
    RuleType.required_field: _required_field,
    RuleType.conditional_required_field: _conditional_required,
    RuleType.date_validation: _date_validation,
    RuleType.numeric_comparison: _numeric_comparison,
    RuleType.amount_calculation: _amount_calculation,
    RuleType.currency_consistency: _currency_consistency,
    RuleType.tax_category_validation: _required_field,
    RuleType.duplicate_field_check: _required_field,
}


def compile_to_xslt(rule: RuleIR) -> str:
    builder = _BUILDERS.get(rule.rule_type, _fallback)
    assertions = builder(rule)
    return _XSLT_WRAPPER.format(
        rule_id=rule.rule_id,
        content_hash=rule.content_hash,
        assertions=assertions,
    )
