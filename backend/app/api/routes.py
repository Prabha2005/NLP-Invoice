from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from app.parser.nl_parser import parse_rule
from app.compiler.xslt_compiler import compile_to_xslt
from app.compiler.validator import validate
from app.models.ir import RuleIR, ValidationResult

router = APIRouter()


# -----------------------------
# Request / Response Models
# -----------------------------

class ParseRequest(BaseModel):
    rule_text: str
    rule_id: str | None = None


class ParseResponse(BaseModel):
    ir: RuleIR
    xslt: str


class ValidateRequest(BaseModel):
    rule_ir: RuleIR
    invoice_xml: str


# -----------------------------
# Parse Endpoint
# -----------------------------

@router.post("/rules/parse", response_model=ParseResponse)
def parse_endpoint(body: ParseRequest):

    try:
        ir = parse_rule(body.rule_text, body.rule_id)

    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    xslt = compile_to_xslt(ir)

    return ParseResponse(
        ir=ir,
        xslt=xslt
    )


# -----------------------------
# Validate Endpoint
# -----------------------------

@router.post("/rules/validate", response_model=list[ValidationResult])
def validate_endpoint(body: ValidateRequest):

    try:
        return validate(body.rule_ir, body.invoice_xml)

    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


# -----------------------------
# Full Pipeline Endpoint
# -----------------------------

@router.post("/rules/run")
async def run_pipeline(
    rule_text: str,
    file: UploadFile = File(...)
):

    invoice_xml = (await file.read()).decode()

    try:
        # Parse English rule into IR
        ir = parse_rule(rule_text)

        # Run validation
        results = validate(ir, invoice_xml)

    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # Summary calculations
    passed = all(result.passed for result in results)

    total_checks = len(results)
    passed_checks = sum(r.passed for r in results)
    failed_checks = sum(not r.passed for r in results)

    # Structured response
    return {
        "status": "PASS" if passed else "FAIL",

        "rule_text": rule_text,

        "ir": ir,

        "summary": {
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
        },

        "results": results,
    }