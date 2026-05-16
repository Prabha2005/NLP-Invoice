"""
Synthetic dataset generator for Complyr (PS-3).

Outputs:
  dataset/rules_train.txt          (100+ rules, JSONL)
  dataset/rules_test.txt           (30+ rules, JSONL)
  dataset/rule_mappings_train.json (IR mapping for each training rule)
  dataset/xml_invoices_train/      (300+ UBL XML invoices)
  dataset/xml_invoices_test/       (100+ UBL XML invoices)
  dataset/validation_labels_train.json
"""

from __future__ import annotations
import json, os, random, hashlib, time
from datetime import date, timedelta
from faker import Faker

fake = Faker()
random.seed(42)

OUT = os.path.dirname(__file__)
TRAIN_INV_DIR = os.path.join(OUT, "xml_invoices_train")
TEST_INV_DIR = os.path.join(OUT, "xml_invoices_test")
os.makedirs(TRAIN_INV_DIR, exist_ok=True)
os.makedirs(TEST_INV_DIR, exist_ok=True)

CURRENCIES = ["AED", "USD", "EUR", "GBP", "SAR"]
TAX_CATEGORIES = ["S", "Z", "E", "AE"]
VALID_COUNTRY_SUBENTITIES = ["DXB", "AUH", "SHJ", "AJM", "RAK"]

UBL_NS = (
    'xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2" '
    'xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2" '
    'xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"'
)


# ---------------------------------------------------------------------------
# Rule templates covering all 8 rule_type values
# ---------------------------------------------------------------------------

RULE_TEMPLATES = [
    # required_field
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cbc:DueDate",
     "rule_text": "Invoice must have a DueDate.",
     "expected_error_message": "DueDate is required."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cbc:BuyerReference",
     "rule_text": "Invoice must include a BuyerReference.",
     "expected_error_message": "BuyerReference is missing."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cbc:CustomizationID",
     "rule_text": "CustomizationID must be present on every invoice.",
     "expected_error_message": "CustomizationID is required."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cbc:InvoiceTypeCode",
     "rule_text": "InvoiceTypeCode must be present.",
     "expected_error_message": "InvoiceTypeCode is required."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cbc:DocumentCurrencyCode",
     "rule_text": "DocumentCurrencyCode must be present.",
     "expected_error_message": "DocumentCurrencyCode is required."},
    {"rule_type": "required_field", "severity": "MEDIUM",
     "field_xpath": "//cac:PaymentMeans",
     "rule_text": "Invoice must include a PaymentMeans block.",
     "expected_error_message": "PaymentMeans block is required."},
    {"rule_type": "required_field", "severity": "MEDIUM",
     "field_xpath": "//cac:PaymentTerms",
     "rule_text": "Invoice must include PaymentTerms.",
     "expected_error_message": "PaymentTerms is required."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cac:AccountingSupplierParty/cac:Party/cac:Contact",
     "rule_text": "Supplier must have a Contact block.",
     "expected_error_message": "Supplier Contact block is missing."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cac:AccountingSupplierParty/cac:Party/cac:PartyIdentification/cbc:ID[@schemeID='CRN']",
     "rule_text": "Supplier must have a CRN PartyIdentification.",
     "expected_error_message": "Supplier CRN PartyIdentification is missing."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cac:AccountingCustomerParty/cac:Party/cac:PartyLegalEntity/cbc:CompanyID",
     "rule_text": "Customer PartyLegalEntity must include a CompanyID.",
     "expected_error_message": "Customer CompanyID is missing."},
    {"rule_type": "required_field", "severity": "MEDIUM",
     "field_xpath": "//cac:AccountingSupplierParty/cac:Party/cac:PostalAddress/cbc:BuildingNumber",
     "rule_text": "Supplier postal address must include BuildingNumber.",
     "expected_error_message": "Supplier BuildingNumber is missing."},
    {"rule_type": "required_field", "severity": "MEDIUM",
     "field_xpath": "//cac:AccountingSupplierParty/cac:Party/cac:PostalAddress/cbc:PostalZone",
     "rule_text": "Supplier postal address must include PostalZone.",
     "expected_error_message": "Supplier PostalZone is missing."},
    # conditional_required_field
    {"rule_type": "conditional_required_field", "severity": "HIGH",
     "field_xpath": "//cbc:TaxExemptionReason",
     "condition_xpath": "//cac:TaxCategory/cbc:ID = 'E'",
     "rule_text": "If tax category is E (exempt), TaxExemptionReason must be present.",
     "expected_error_message": "TaxExemptionReason required when tax category is E."},
    {"rule_type": "conditional_required_field", "severity": "HIGH",
     "field_xpath": "//cbc:TaxExemptionReasonCode",
     "condition_xpath": "//cac:TaxCategory/cbc:ID = 'Z'",
     "rule_text": "If tax category is Z (zero-rated), TaxExemptionReasonCode must be present.",
     "expected_error_message": "TaxExemptionReasonCode required for zero-rated tax."},
    {"rule_type": "conditional_required_field", "severity": "MEDIUM",
     "field_xpath": "//cac:PayeeFinancialAccount/cbc:ID",
     "condition_xpath": "//cac:PaymentMeans/cbc:PaymentMeansCode = '30'",
     "rule_text": "If PaymentMeansCode is 30 (bank transfer), PayeeFinancialAccount ID must be present.",
     "expected_error_message": "PayeeFinancialAccount required for bank transfer payment."},
    # date_validation
    {"rule_type": "date_validation", "severity": "HIGH",
     "field_xpath": "//cbc:IssueDate",
     "rule_text": "IssueDate must be a valid date in YYYY-MM-DD format.",
     "expected_error_message": "IssueDate is invalid or missing."},
    {"rule_type": "date_validation", "severity": "MEDIUM",
     "field_xpath": "//cbc:DueDate",
     "rule_text": "DueDate must be a valid date in YYYY-MM-DD format.",
     "expected_error_message": "DueDate is invalid or malformed."},
    {"rule_type": "date_validation", "severity": "HIGH",
     "field_xpath": "//cbc:IssueDate",
     "rule_text": "IssueDate must not be in the future.",
     "expected_error_message": "IssueDate cannot be a future date."},
    # numeric_comparison
    {"rule_type": "numeric_comparison", "severity": "HIGH",
     "field_xpath": "//cac:LegalMonetaryTotal/cbc:PayableAmount",
     "operator": "gt", "expected_value": 0,
     "rule_text": "PayableAmount must be greater than zero.",
     "expected_error_message": "PayableAmount must be positive."},
    {"rule_type": "numeric_comparison", "severity": "HIGH",
     "field_xpath": "//cac:TaxTotal/cbc:TaxAmount",
     "operator": "gte", "expected_value": 0,
     "rule_text": "TaxAmount must be zero or greater.",
     "expected_error_message": "TaxAmount cannot be negative."},
    {"rule_type": "numeric_comparison", "severity": "MEDIUM",
     "field_xpath": "//cac:TaxSubtotal/cbc:Percent",
     "operator": "lte", "expected_value": 28,
     "rule_text": "Tax percentage must not exceed 28%.",
     "expected_error_message": "Tax percentage exceeds 28%."},
    {"rule_type": "numeric_comparison", "severity": "HIGH",
     "field_xpath": "//cbc:InvoicedQuantity",
     "operator": "gt", "expected_value": 0,
     "rule_text": "InvoicedQuantity must be greater than zero.",
     "expected_error_message": "InvoicedQuantity must be positive."},
    # amount_calculation
    {"rule_type": "amount_calculation", "severity": "HIGH",
     "field_xpath": "//cac:LegalMonetaryTotal/cbc:TaxInclusiveAmount",
     "condition_xpath": "number(//cac:LegalMonetaryTotal/cbc:TaxInclusiveAmount) = number(//cac:LegalMonetaryTotal/cbc:TaxExclusiveAmount) + number(//cac:TaxTotal/cbc:TaxAmount)",
     "rule_text": "TaxInclusiveAmount must equal TaxExclusiveAmount plus TaxAmount.",
     "expected_error_message": "TaxInclusiveAmount does not match TaxExclusiveAmount + TaxAmount."},
    {"rule_type": "amount_calculation", "severity": "HIGH",
     "field_xpath": "//cac:LegalMonetaryTotal/cbc:PayableAmount",
     "condition_xpath": "number(//cac:LegalMonetaryTotal/cbc:PayableAmount) = number(//cac:LegalMonetaryTotal/cbc:TaxInclusiveAmount)",
     "rule_text": "PayableAmount must equal TaxInclusiveAmount.",
     "expected_error_message": "PayableAmount does not match TaxInclusiveAmount."},
    {"rule_type": "amount_calculation", "severity": "HIGH",
     "field_xpath": "//cac:LegalMonetaryTotal/cbc:LineExtensionAmount",
     "condition_xpath": "number(//cac:LegalMonetaryTotal/cbc:LineExtensionAmount) = sum(//cac:InvoiceLine/cbc:LineExtensionAmount)",
     "rule_text": "LineExtensionAmount total must equal sum of all invoice line amounts.",
     "expected_error_message": "LineExtensionAmount total does not match sum of invoice lines."},
    # currency_consistency
    {"rule_type": "currency_consistency", "severity": "HIGH",
     "field_xpath": "//cbc:DocumentCurrencyCode",
     "rule_text": "All monetary amounts must use the same currency as DocumentCurrencyCode.",
     "expected_error_message": "Currency mismatch detected on a monetary field."},
    {"rule_type": "currency_consistency", "severity": "HIGH",
     "field_xpath": "//cbc:DocumentCurrencyCode",
     "rule_text": "TaxAmount currency must match DocumentCurrencyCode.",
     "expected_error_message": "TaxAmount currency does not match DocumentCurrencyCode."},
    # tax_category_validation
    {"rule_type": "tax_category_validation", "severity": "HIGH",
     "field_xpath": "//cac:TaxCategory/cbc:ID",
     "rule_text": "Tax category ID must be one of S, Z, E, or AE.",
     "expected_error_message": "Tax category ID is not a recognised value."},
    {"rule_type": "tax_category_validation", "severity": "HIGH",
     "field_xpath": "//cac:ClassifiedTaxCategory/cbc:ID",
     "rule_text": "Each invoice line must have a ClassifiedTaxCategory ID.",
     "expected_error_message": "ClassifiedTaxCategory ID is missing on an invoice line."},
    # duplicate_field_check
    {"rule_type": "duplicate_field_check", "severity": "HIGH",
     "field_xpath": "//cbc:ID[parent::Invoice]",
     "rule_text": "Invoice ID must be unique across the batch.",
     "expected_error_message": "Duplicate invoice ID detected."},
    {"rule_type": "duplicate_field_check", "severity": "MEDIUM",
     "field_xpath": "//cac:InvoiceLine/cbc:ID",
     "rule_text": "Invoice line IDs must be unique within the same invoice.",
     "expected_error_message": "Duplicate line ID found within invoice."},
]

# Expand to 100+ by paraphrasing the base set
EXTRA_RULES = [
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cbc:ProfileID",
     "rule_text": "ProfileID must be present on every invoice.",
     "expected_error_message": "ProfileID is required."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cbc:IssueDate",
     "rule_text": "IssueDate is mandatory.",
     "expected_error_message": "IssueDate is missing."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID",
     "rule_text": "Supplier VAT registration number (CompanyID) must be present.",
     "expected_error_message": "Supplier CompanyID (VAT) is missing."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cac:AccountingSupplierParty/cac:Party/cac:PartyName/cbc:Name",
     "rule_text": "Supplier name must be present.",
     "expected_error_message": "Supplier name is missing."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cac:AccountingCustomerParty/cac:Party/cac:PartyName/cbc:Name",
     "rule_text": "Customer name must be present.",
     "expected_error_message": "Customer name is missing."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cac:LegalMonetaryTotal/cbc:PayableAmount",
     "rule_text": "PayableAmount must be present in LegalMonetaryTotal.",
     "expected_error_message": "PayableAmount is missing."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cac:TaxTotal/cbc:TaxAmount",
     "rule_text": "TaxTotal must include a TaxAmount.",
     "expected_error_message": "TaxAmount is missing from TaxTotal."},
    {"rule_type": "required_field", "severity": "MEDIUM",
     "field_xpath": "//cac:InvoiceLine/cac:Item/cbc:Name",
     "rule_text": "Each invoice line item must have a Name.",
     "expected_error_message": "Item Name is missing on an invoice line."},
    {"rule_type": "required_field", "severity": "MEDIUM",
     "field_xpath": "//cac:InvoiceLine/cac:Price/cbc:PriceAmount",
     "rule_text": "Each invoice line must include a PriceAmount.",
     "expected_error_message": "PriceAmount is missing on an invoice line."},
    {"rule_type": "required_field", "severity": "LOW",
     "field_xpath": "//cac:AccountingSupplierParty/cac:Party/cac:PostalAddress/cbc:CityName",
     "rule_text": "Supplier postal address must include a CityName.",
     "expected_error_message": "Supplier CityName is missing."},
    {"rule_type": "required_field", "severity": "LOW",
     "field_xpath": "//cac:AccountingSupplierParty/cac:Party/cac:PostalAddress/cbc:StreetName",
     "rule_text": "Supplier postal address must include a StreetName.",
     "expected_error_message": "Supplier StreetName is missing."},
    {"rule_type": "numeric_comparison", "severity": "HIGH",
     "field_xpath": "//cac:LegalMonetaryTotal/cbc:TaxExclusiveAmount",
     "operator": "gte", "expected_value": 0,
     "rule_text": "TaxExclusiveAmount must be zero or greater.",
     "expected_error_message": "TaxExclusiveAmount cannot be negative."},
    {"rule_type": "numeric_comparison", "severity": "MEDIUM",
     "field_xpath": "//cac:TaxSubtotal/cbc:Percent",
     "operator": "gte", "expected_value": 0,
     "rule_text": "Tax percent must not be negative.",
     "expected_error_message": "Tax percent is negative."},
    {"rule_type": "date_validation", "severity": "MEDIUM",
     "field_xpath": "//cbc:DueDate",
     "rule_text": "DueDate must be after IssueDate.",
     "expected_error_message": "DueDate must be after IssueDate."},
    {"rule_type": "conditional_required_field", "severity": "HIGH",
     "field_xpath": "//cac:AccountingCustomerParty/cac:Party/cac:PartyIdentification/cbc:ID[@schemeID='CRN']",
     "condition_xpath": "//cbc:DocumentCurrencyCode = 'AED'",
     "rule_text": "For AED invoices, customer must have a CRN PartyIdentification.",
     "expected_error_message": "Customer CRN required for AED invoices."},
    {"rule_type": "tax_category_validation", "severity": "HIGH",
     "field_xpath": "//cac:TaxSubtotal/cac:TaxCategory/cbc:ID",
     "rule_text": "TaxSubtotal must contain a TaxCategory ID.",
     "expected_error_message": "TaxSubtotal TaxCategory ID is missing."},
    {"rule_type": "amount_calculation", "severity": "HIGH",
     "field_xpath": "//cac:TaxTotal/cbc:TaxAmount",
     "condition_xpath": "number(//cac:TaxTotal/cbc:TaxAmount) = number(//cac:LegalMonetaryTotal/cbc:TaxExclusiveAmount) * number(//cac:TaxSubtotal/cbc:Percent) div 100",
     "rule_text": "TaxAmount must equal TaxableAmount multiplied by the tax percentage divided by 100.",
     "expected_error_message": "TaxAmount does not match taxable amount times tax rate."},
    {"rule_type": "currency_consistency", "severity": "HIGH",
     "field_xpath": "//cbc:DocumentCurrencyCode",
     "rule_text": "PayableAmount currency must match DocumentCurrencyCode.",
     "expected_error_message": "PayableAmount currency does not match DocumentCurrencyCode."},
    {"rule_type": "duplicate_field_check", "severity": "HIGH",
     "field_xpath": "//cac:InvoiceLine/cbc:ID",
     "rule_text": "Line IDs within an invoice must not repeat.",
     "expected_error_message": "Repeated line ID found in invoice."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cac:AccountingSupplierParty/cac:Party/cbc:EndpointID",
     "rule_text": "Supplier EndpointID must be present.",
     "expected_error_message": "Supplier EndpointID is missing."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cac:AccountingCustomerParty/cac:Party/cbc:EndpointID",
     "rule_text": "Customer EndpointID must be present.",
     "expected_error_message": "Customer EndpointID is missing."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity/cbc:RegistrationName",
     "rule_text": "Supplier legal registration name must be present.",
     "expected_error_message": "Supplier RegistrationName is missing."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cac:AccountingCustomerParty/cac:Party/cac:PartyLegalEntity/cbc:RegistrationName",
     "rule_text": "Customer legal registration name must be present.",
     "expected_error_message": "Customer RegistrationName is missing."},
    {"rule_type": "numeric_comparison", "severity": "HIGH",
     "field_xpath": "//cbc:LineExtensionAmount",
     "operator": "gte", "expected_value": 0,
     "rule_text": "LineExtensionAmount on each line must be zero or greater.",
     "expected_error_message": "LineExtensionAmount cannot be negative."},
    {"rule_type": "required_field", "severity": "MEDIUM",
     "field_xpath": "//cac:InvoiceLine/cac:Item/cbc:Description",
     "rule_text": "Each invoice line item should include a Description.",
     "expected_error_message": "Item Description is missing on an invoice line."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cac:TaxSubtotal/cbc:TaxableAmount",
     "rule_text": "TaxSubtotal must include TaxableAmount.",
     "expected_error_message": "TaxableAmount is missing from TaxSubtotal."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cac:LegalMonetaryTotal/cbc:TaxExclusiveAmount",
     "rule_text": "LegalMonetaryTotal must include TaxExclusiveAmount.",
     "expected_error_message": "TaxExclusiveAmount is missing."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cac:LegalMonetaryTotal/cbc:TaxInclusiveAmount",
     "rule_text": "LegalMonetaryTotal must include TaxInclusiveAmount.",
     "expected_error_message": "TaxInclusiveAmount is missing."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cac:LegalMonetaryTotal/cbc:LineExtensionAmount",
     "rule_text": "LegalMonetaryTotal must include LineExtensionAmount.",
     "expected_error_message": "LineExtensionAmount is missing from LegalMonetaryTotal."},
    {"rule_type": "conditional_required_field", "severity": "HIGH",
     "field_xpath": "//cac:AllowanceCharge/cbc:Amount",
     "condition_xpath": "//cac:AllowanceCharge",
     "rule_text": "If AllowanceCharge is present, Amount must be included.",
     "expected_error_message": "AllowanceCharge Amount is missing."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cac:AccountingSupplierParty/cac:Party/cac:PostalAddress/cac:Country/cbc:IdentificationCode",
     "rule_text": "Supplier country identification code must be present.",
     "expected_error_message": "Supplier country code is missing."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cac:AccountingCustomerParty/cac:Party/cac:PostalAddress/cac:Country/cbc:IdentificationCode",
     "rule_text": "Customer country identification code must be present.",
     "expected_error_message": "Customer country code is missing."},
    {"rule_type": "required_field", "severity": "MEDIUM",
     "field_xpath": "//cac:PaymentMeans/cbc:PaymentMeansCode",
     "rule_text": "PaymentMeans must include a PaymentMeansCode.",
     "expected_error_message": "PaymentMeansCode is missing."},
    {"rule_type": "numeric_comparison", "severity": "HIGH",
     "field_xpath": "//cbc:PriceAmount",
     "operator": "gt", "expected_value": 0,
     "rule_text": "PriceAmount on each line must be greater than zero.",
     "expected_error_message": "PriceAmount must be positive."},
    {"rule_type": "tax_category_validation", "severity": "HIGH",
     "field_xpath": "//cac:TaxCategory/cac:TaxScheme/cbc:ID",
     "rule_text": "TaxScheme ID must be present within TaxCategory.",
     "expected_error_message": "TaxScheme ID is missing in TaxCategory."},
    {"rule_type": "required_field", "severity": "LOW",
     "field_xpath": "//cac:AccountingCustomerParty/cac:Party/cac:PostalAddress/cbc:CityName",
     "rule_text": "Customer postal address must include a CityName.",
     "expected_error_message": "Customer CityName is missing."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cac:TaxScheme/cbc:ID",
     "rule_text": "Supplier TaxScheme ID must be present.",
     "expected_error_message": "Supplier TaxScheme ID is missing."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cac:AccountingCustomerParty/cac:Party/cac:PartyTaxScheme/cac:TaxScheme/cbc:ID",
     "rule_text": "Customer TaxScheme ID must be present.",
     "expected_error_message": "Customer TaxScheme ID is missing."},
]

EXTRA_RULES_2 = [
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cac:InvoiceLine/cbc:ID",
     "rule_text": "Each invoice line must have an ID.",
     "expected_error_message": "Invoice line ID is missing."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cac:InvoiceLine/cbc:InvoicedQuantity",
     "rule_text": "Each invoice line must have an InvoicedQuantity.",
     "expected_error_message": "InvoicedQuantity is missing on a line."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cac:InvoiceLine/cbc:LineExtensionAmount",
     "rule_text": "Each invoice line must have a LineExtensionAmount.",
     "expected_error_message": "LineExtensionAmount is missing on a line."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID",
     "rule_text": "Supplier tax scheme CompanyID must be provided.",
     "expected_error_message": "Supplier tax CompanyID missing."},
    {"rule_type": "required_field", "severity": "MEDIUM",
     "field_xpath": "//cac:AccountingCustomerParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID",
     "rule_text": "Customer tax scheme CompanyID must be provided.",
     "expected_error_message": "Customer tax CompanyID missing."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cac:TaxSubtotal/cac:TaxCategory/cbc:Percent",
     "rule_text": "TaxSubtotal TaxCategory must include Percent.",
     "expected_error_message": "Tax percent missing from TaxSubtotal."},
    {"rule_type": "numeric_comparison", "severity": "HIGH",
     "field_xpath": "//cbc:BaseQuantity",
     "operator": "gt", "expected_value": 0,
     "rule_text": "BaseQuantity on each line must be greater than zero.",
     "expected_error_message": "BaseQuantity must be positive."},
    {"rule_type": "required_field", "severity": "MEDIUM",
     "field_xpath": "//cac:PaymentTerms/cbc:Note",
     "rule_text": "PaymentTerms must include a Note.",
     "expected_error_message": "PaymentTerms Note is missing."},
    {"rule_type": "required_field", "severity": "LOW",
     "field_xpath": "//cac:AccountingSupplierParty/cac:Party/cac:PostalAddress/cbc:CountrySubentity",
     "rule_text": "Supplier postal address must include CountrySubentity.",
     "expected_error_message": "Supplier CountrySubentity is missing."},
    {"rule_type": "required_field", "severity": "LOW",
     "field_xpath": "//cac:AccountingCustomerParty/cac:Party/cac:PostalAddress/cbc:CountrySubentity",
     "rule_text": "Customer postal address must include CountrySubentity.",
     "expected_error_message": "Customer CountrySubentity is missing."},
    {"rule_type": "numeric_comparison", "severity": "MEDIUM",
     "field_xpath": "//cac:LegalMonetaryTotal/cbc:TaxInclusiveAmount",
     "operator": "gte", "expected_value": 0,
     "rule_text": "TaxInclusiveAmount must be zero or greater.",
     "expected_error_message": "TaxInclusiveAmount cannot be negative."},
    {"rule_type": "conditional_required_field", "severity": "HIGH",
     "field_xpath": "//cac:PaymentMeans/cac:PayeeFinancialAccount/cbc:ID",
     "condition_xpath": "//cac:PaymentMeans/cbc:PaymentMeansCode = '30'",
     "rule_text": "Bank transfer invoices must include a PayeeFinancialAccount ID.",
     "expected_error_message": "PayeeFinancialAccount ID required for bank transfer."},
    {"rule_type": "date_validation", "severity": "HIGH",
     "field_xpath": "//cbc:IssueDate",
     "rule_text": "IssueDate must not be empty.",
     "expected_error_message": "IssueDate cannot be empty."},
    {"rule_type": "tax_category_validation", "severity": "HIGH",
     "field_xpath": "//cac:ClassifiedTaxCategory/cac:TaxScheme/cbc:ID",
     "rule_text": "Each line ClassifiedTaxCategory must include TaxScheme ID.",
     "expected_error_message": "TaxScheme ID missing in ClassifiedTaxCategory."},
    {"rule_type": "amount_calculation", "severity": "HIGH",
     "field_xpath": "//cac:LegalMonetaryTotal/cbc:TaxExclusiveAmount",
     "condition_xpath": "number(//cac:LegalMonetaryTotal/cbc:TaxExclusiveAmount) = number(//cac:LegalMonetaryTotal/cbc:LineExtensionAmount)",
     "rule_text": "TaxExclusiveAmount must equal LineExtensionAmount when no allowances apply.",
     "expected_error_message": "TaxExclusiveAmount does not match LineExtensionAmount."},
    {"rule_type": "currency_consistency", "severity": "HIGH",
     "field_xpath": "//cbc:DocumentCurrencyCode",
     "rule_text": "TaxableAmount currency must match DocumentCurrencyCode.",
     "expected_error_message": "TaxableAmount currency mismatch."},
    {"rule_type": "currency_consistency", "severity": "HIGH",
     "field_xpath": "//cbc:DocumentCurrencyCode",
     "rule_text": "LineExtensionAmount currency on all lines must match DocumentCurrencyCode.",
     "expected_error_message": "LineExtensionAmount currency mismatch on invoice line."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity/cbc:CompanyID",
     "rule_text": "Supplier PartyLegalEntity must include CompanyID.",
     "expected_error_message": "Supplier PartyLegalEntity CompanyID missing."},
    {"rule_type": "numeric_comparison", "severity": "HIGH",
     "field_xpath": "//cac:LegalMonetaryTotal/cbc:LineExtensionAmount",
     "operator": "gte", "expected_value": 0,
     "rule_text": "Total LineExtensionAmount must be zero or greater.",
     "expected_error_message": "Total LineExtensionAmount cannot be negative."},
    {"rule_type": "duplicate_field_check", "severity": "MEDIUM",
     "field_xpath": "//cac:AccountingSupplierParty/cac:Party/cbc:EndpointID",
     "rule_text": "Supplier EndpointID must not be duplicated across invoices in a batch.",
     "expected_error_message": "Duplicate Supplier EndpointID in batch."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cac:InvoiceLine/cac:Item",
     "rule_text": "Each invoice line must include an Item block.",
     "expected_error_message": "Item block missing on invoice line."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cac:InvoiceLine/cac:Price",
     "rule_text": "Each invoice line must include a Price block.",
     "expected_error_message": "Price block missing on invoice line."},
    {"rule_type": "conditional_required_field", "severity": "MEDIUM",
     "field_xpath": "//cbc:Note",
     "condition_xpath": "//cbc:InvoiceTypeCode = '381'",
     "rule_text": "Credit notes must include a Note explaining the reason.",
     "expected_error_message": "Note required for credit note invoices."},
    {"rule_type": "numeric_comparison", "severity": "HIGH",
     "field_xpath": "//cbc:TaxAmount",
     "operator": "lte", "expected_value": 999999999,
     "rule_text": "TaxAmount must not exceed a reasonable maximum.",
     "expected_error_message": "TaxAmount exceeds maximum allowed value."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cbc:ID",
     "rule_text": "Invoice ID must be present.",
     "expected_error_message": "Invoice ID is missing."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cac:TaxTotal",
     "rule_text": "Invoice must include a TaxTotal block.",
     "expected_error_message": "TaxTotal block is required."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cac:LegalMonetaryTotal",
     "rule_text": "Invoice must include a LegalMonetaryTotal block.",
     "expected_error_message": "LegalMonetaryTotal block is required."},
    {"rule_type": "required_field", "severity": "HIGH",
     "field_xpath": "//cac:InvoiceLine",
     "rule_text": "Invoice must have at least one InvoiceLine.",
     "expected_error_message": "No InvoiceLine found on invoice."},
    {"rule_type": "date_validation", "severity": "MEDIUM",
     "field_xpath": "//cbc:IssueDate",
     "rule_text": "IssueDate must follow the format YYYY-MM-DD.",
     "expected_error_message": "IssueDate format is invalid."},
    {"rule_type": "tax_category_validation", "severity": "MEDIUM",
     "field_xpath": "//cac:TaxCategory/cbc:Percent",
     "rule_text": "TaxCategory must include a Percent value.",
     "expected_error_message": "Tax percent missing from TaxCategory."},
    {"rule_type": "conditional_required_field", "severity": "HIGH",
     "field_xpath": "//cbc:TaxExemptionReason",
     "condition_xpath": "//cac:TaxCategory/cbc:ID = 'AE'",
     "rule_text": "Reverse charge invoices must include TaxExemptionReason.",
     "expected_error_message": "TaxExemptionReason required for reverse charge."},
]

ALL_RULES_RAW = RULE_TEMPLATES + EXTRA_RULES + EXTRA_RULES_2


def build_rules(raw: list[dict], id_prefix: str) -> list[dict]:
    rules = []
    for i, r in enumerate(raw):
        rule_id = f"{id_prefix}-{i+1:03d}"
        entry = {
            "rule_id": rule_id,
            "rule_text": r["rule_text"],
            "severity": r["severity"],
            "rule_type": r["rule_type"],
            "expected_error_message": r["expected_error_message"],
            "field_xpath": r.get("field_xpath", ""),
            "condition_xpath": r.get("condition_xpath"),
            "expected_value": r.get("expected_value"),
            "operator": r.get("operator"),
        }
        rules.append(entry)
    return rules


# ---------------------------------------------------------------------------
# Invoice generator
# ---------------------------------------------------------------------------

def make_invoice(inv_id: str, force_invalid: bool = False) -> tuple[str, dict]:
    currency = random.choice(CURRENCIES)
    issue_date = date.today() - timedelta(days=random.randint(1, 365))
    due_date = issue_date + timedelta(days=random.randint(7, 90))

    n_lines = random.randint(1, 10)
    lines = []
    line_total = 0.0
    for ln in range(1, n_lines + 1):
        qty = random.randint(1, 20)
        price = round(random.uniform(5, 5000), 2)
        line_ext = round(qty * price, 2)
        line_total += line_ext
        lines.append((ln, qty, price, line_ext, random.choice(TAX_CATEGORIES)))

    taxable = round(line_total, 2)
    tax_pct = random.choice([0, 5, 10, 15, 20, 28])
    tax_amt = round(taxable * tax_pct / 100, 2)
    tax_incl = round(taxable + tax_amt, 2)
    payable = tax_incl

    seller = fake.company()
    buyer = fake.company()
    seller_trn = str(random.randint(100000000000000, 999999999999999))
    buyer_trn = str(random.randint(100000000000000, 999999999999999))
    subentity = random.choice(VALID_COUNTRY_SUBENTITIES)

    faults: list[str] = []

    if force_invalid:
        fault = random.choice([
            "missing_due_date", "missing_buyer_ref", "future_issue_date",
            "wrong_payable", "wrong_tax_amt", "wrong_customization_id",
            "missing_payment_means", "wrong_currency_on_line",
            "missing_supplier_contact", "wrong_country_subentity",
        ])
        faults.append(fault)

    due_date_str = due_date.isoformat()
    buyer_ref = f"PO-{random.randint(10000,99999)}"
    customization_id = "urn:peppol:pint:billing-1@ae-1"
    issue_date_str = issue_date.isoformat()

    if "missing_due_date" in faults:
        due_date_str = ""
    if "missing_buyer_ref" in faults:
        buyer_ref = ""
    if "future_issue_date" in faults:
        issue_date_str = (date.today() + timedelta(days=30)).isoformat()
    if "wrong_payable" in faults:
        payable = round(payable * 1.1 + 99, 2)
    if "wrong_tax_amt" in faults:
        tax_amt = round(tax_amt * 2, 2)
    if "wrong_customization_id" in faults:
        customization_id = "urn:peppol:pint:billing-1@ae-X"
    if "wrong_currency_on_line" in faults:
        bad_currency = random.choice([c for c in CURRENCIES if c != currency])
        lines[0] = (lines[0][0], lines[0][1], lines[0][2], lines[0][3], lines[0][4])
        currency_override = bad_currency
    else:
        currency_override = currency
    if "wrong_country_subentity" in faults:
        subentity = "DUBAI"

    def line_xml(ln_num, qty, price, line_ext, tax_cat):
        cur = currency_override if (ln_num == 1 and "wrong_currency_on_line" in faults) else currency
        return f"""  <cac:InvoiceLine>
    <cbc:ID>{ln_num}</cbc:ID>
    <cbc:InvoicedQuantity unitCode="EA">{qty}</cbc:InvoicedQuantity>
    <cbc:LineExtensionAmount currencyID="{cur}">{line_ext:.2f}</cbc:LineExtensionAmount>
    <cac:Item>
      <cbc:Description>{fake.bs()}</cbc:Description>
      <cbc:Name>{fake.catch_phrase()[:40]}</cbc:Name>
      <cac:ClassifiedTaxCategory>
        <cbc:ID>{tax_cat}</cbc:ID>
        <cbc:Percent>{tax_pct}.00</cbc:Percent>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
      </cac:ClassifiedTaxCategory>
    </cac:Item>
    <cac:Price>
      <cbc:PriceAmount currencyID="{cur}">{price:.2f}</cbc:PriceAmount>
      <cbc:BaseQuantity unitCode="EA">1</cbc:BaseQuantity>
    </cac:Price>
  </cac:InvoiceLine>"""

    contact_block = "" if "missing_supplier_contact" in faults else f"""      <cac:Contact>
        <cbc:Name>Accounts Receivable</cbc:Name>
        <cbc:Telephone>{fake.phone_number()}</cbc:Telephone>
        <cbc:ElectronicMail>{fake.company_email()}</cbc:ElectronicMail>
      </cac:Contact>"""

    payment_means_block = "" if "missing_payment_means" in faults else f"""  <cac:PaymentMeans>
    <cbc:PaymentMeansCode>30</cbc:PaymentMeansCode>
    <cbc:PaymentID>BANK-TRF-{inv_id}</cbc:PaymentID>
    <cac:PayeeFinancialAccount>
      <cbc:ID>AE{random.randint(10,99)}{random.randint(10**20,10**21-1)}</cbc:ID>
      <cbc:Name>{seller}</cbc:Name>
    </cac:PayeeFinancialAccount>
  </cac:PaymentMeans>"""

    due_elem = f"  <cbc:DueDate>{due_date_str}</cbc:DueDate>" if due_date_str else ""
    buyer_ref_elem = f"  <cbc:BuyerReference>{buyer_ref}</cbc:BuyerReference>" if buyer_ref else ""

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice {UBL_NS}>
  <cbc:CustomizationID>{customization_id}</cbc:CustomizationID>
  <cbc:ProfileID>urn:peppol:bis:billing:01:1.0</cbc:ProfileID>
  <cbc:ID>{inv_id}</cbc:ID>
  <cbc:IssueDate>{issue_date_str}</cbc:IssueDate>
{due_elem}
  <cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode>
  <cbc:DocumentCurrencyCode>{currency}</cbc:DocumentCurrencyCode>
{buyer_ref_elem}

  <cac:AccountingSupplierParty>
    <cac:Party>
      <cbc:EndpointID schemeID="0235">{seller_trn}</cbc:EndpointID>
      <cac:PartyIdentification>
        <cbc:ID schemeID="CRN">CN-{random.randint(1000000,9999999)}</cbc:ID>
      </cac:PartyIdentification>
      <cac:PartyName><cbc:Name>{seller}</cbc:Name></cac:PartyName>
      <cac:PostalAddress>
        <cbc:StreetName>{fake.street_address()}</cbc:StreetName>
        <cbc:BuildingNumber>{random.randint(1,999)}</cbc:BuildingNumber>
        <cbc:CityName>{fake.city()}</cbc:CityName>
        <cbc:PostalZone>{fake.postcode()[:5]}</cbc:PostalZone>
        <cbc:CountrySubentity>{subentity}</cbc:CountrySubentity>
        <cac:Country><cbc:IdentificationCode>AE</cbc:IdentificationCode></cac:Country>
      </cac:PostalAddress>
      <cac:PartyTaxScheme>
        <cbc:CompanyID>{seller_trn}</cbc:CompanyID>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
      </cac:PartyTaxScheme>
      <cac:PartyLegalEntity>
        <cbc:RegistrationName>{seller}</cbc:RegistrationName>
        <cbc:CompanyID schemeAgencyID="PAS" schemeAgencyName="AE">CN-{random.randint(1000000,9999999)}</cbc:CompanyID>
      </cac:PartyLegalEntity>
{contact_block}
    </cac:Party>
  </cac:AccountingSupplierParty>

  <cac:AccountingCustomerParty>
    <cac:Party>
      <cbc:EndpointID schemeID="0235">{buyer_trn}</cbc:EndpointID>
      <cac:PartyIdentification>
        <cbc:ID schemeID="CRN">CN-{random.randint(1000000,9999999)}</cbc:ID>
      </cac:PartyIdentification>
      <cac:PartyName><cbc:Name>{buyer}</cbc:Name></cac:PartyName>
      <cac:PostalAddress>
        <cbc:StreetName>{fake.street_address()}</cbc:StreetName>
        <cbc:BuildingNumber>{random.randint(1,999)}</cbc:BuildingNumber>
        <cbc:CityName>{fake.city()}</cbc:CityName>
        <cbc:PostalZone>{fake.postcode()[:5]}</cbc:PostalZone>
        <cbc:CountrySubentity>{random.choice(VALID_COUNTRY_SUBENTITIES)}</cbc:CountrySubentity>
        <cac:Country><cbc:IdentificationCode>AE</cbc:IdentificationCode></cac:Country>
      </cac:PostalAddress>
      <cac:PartyTaxScheme>
        <cbc:CompanyID>{buyer_trn}</cbc:CompanyID>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
      </cac:PartyTaxScheme>
      <cac:PartyLegalEntity>
        <cbc:RegistrationName>{buyer}</cbc:RegistrationName>
        <cbc:CompanyID schemeAgencyID="PAS" schemeAgencyName="AE">CN-{random.randint(1000000,9999999)}</cbc:CompanyID>
      </cac:PartyLegalEntity>
    </cac:Party>
  </cac:AccountingCustomerParty>

{payment_means_block}

  <cac:PaymentTerms>
    <cbc:Note>Payable within 30 days from invoice date.</cbc:Note>
  </cac:PaymentTerms>

  <cac:TaxTotal>
    <cbc:TaxAmount currencyID="{currency}">{tax_amt:.2f}</cbc:TaxAmount>
    <cac:TaxSubtotal>
      <cbc:TaxableAmount currencyID="{currency}">{taxable:.2f}</cbc:TaxableAmount>
      <cbc:TaxAmount currencyID="{currency}">{tax_amt:.2f}</cbc:TaxAmount>
      <cac:TaxCategory>
        <cbc:ID>{lines[0][4]}</cbc:ID>
        <cbc:Percent>{tax_pct}.00</cbc:Percent>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme>
      </cac:TaxCategory>
    </cac:TaxSubtotal>
  </cac:TaxTotal>

  <cac:LegalMonetaryTotal>
    <cbc:LineExtensionAmount currencyID="{currency}">{taxable:.2f}</cbc:LineExtensionAmount>
    <cbc:TaxExclusiveAmount currencyID="{currency}">{taxable:.2f}</cbc:TaxExclusiveAmount>
    <cbc:TaxInclusiveAmount currencyID="{currency}">{tax_incl:.2f}</cbc:TaxInclusiveAmount>
    <cbc:PayableAmount currencyID="{currency}">{payable:.2f}</cbc:PayableAmount>
  </cac:LegalMonetaryTotal>

{"".join(line_xml(*l) for l in lines)}
</Invoice>"""

    label = {
        "invoice_id": inv_id,
        "is_valid": len(faults) == 0,
        "faults": faults,
        "currency": currency,
        "taxable_amount": taxable,
        "tax_amount": tax_amt,
        "payable_amount": payable,
        "seller_name": seller,
        "buyer_name": buyer,
    }
    return xml, label


def generate_invoices(n: int, out_dir: str, prefix: str, invalid_rate: float = 0.4) -> list[dict]:
    labels = []
    ids_used = set()
    for i in range(n):
        while True:
            inv_id = f"{prefix}-{i+1:05d}-{random.randint(1000,9999)}"
            if inv_id not in ids_used:
                ids_used.add(inv_id)
                break
        force_invalid = random.random() < invalid_rate
        xml, label = make_invoice(inv_id, force_invalid)
        path = os.path.join(out_dir, f"{inv_id}.xml")
        with open(path, "w", encoding="utf-8") as f:
            f.write(xml)
        labels.append(label)
    return labels


def content_hash(r: dict) -> str:
    payload = {k: r[k] for k in ("rule_type", "field_xpath", "condition_xpath", "expected_value", "operator")}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


if __name__ == "__main__":
    print("Building rule sets...")
    train_rules = build_rules(ALL_RULES_RAW, "TR")
    test_rules = build_rules(random.sample(ALL_RULES_RAW, 35), "TE")

    with open(os.path.join(OUT, "rules_train.txt"), "w") as f:
        for r in train_rules:
            f.write(json.dumps({k: r[k] for k in ("rule_id","rule_text","severity","rule_type","expected_error_message")}) + "\n")

    with open(os.path.join(OUT, "rules_test.txt"), "w") as f:
        for r in test_rules:
            f.write(json.dumps({k: r[k] for k in ("rule_id","rule_text","severity","rule_type","expected_error_message")}) + "\n")

    mappings = []
    for r in train_rules:
        mappings.append({
            "rule_id": r["rule_id"],
            "rule_text": r["rule_text"],
            "rule_type": r["rule_type"],
            "severity": r["severity"],
            "field_xpath": r["field_xpath"],
            "condition_xpath": r.get("condition_xpath"),
            "expected_value": r.get("expected_value"),
            "operator": r.get("operator"),
            "expected_error_message": r["expected_error_message"],
            "content_hash": content_hash(r),
        })
    with open(os.path.join(OUT, "rule_mappings_train.json"), "w") as f:
        json.dump(mappings, f, indent=2)

    print(f"Generated {len(train_rules)} training rules, {len(test_rules)} test rules.")

    print("Generating training invoices (300)...")
    train_labels = generate_invoices(300, TRAIN_INV_DIR, "TRAIN", invalid_rate=0.4)

    print("Generating test invoices (100)...")
    test_labels = generate_invoices(100, TEST_INV_DIR, "TEST", invalid_rate=0.4)

    with open(os.path.join(OUT, "validation_labels_train.json"), "w") as f:
        json.dump(train_labels, f, indent=2)

    valid_count = sum(1 for l in train_labels if l["is_valid"])
    invalid_count = len(train_labels) - valid_count
    print(f"Training invoices: {valid_count} valid, {invalid_count} invalid.")
    print("Done. All dataset files written to dataset/")
