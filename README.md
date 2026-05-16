# PS-3: Natural Language Rule Engine for XML Invoice Validation

# Description

Tax-compliant e-invoicing systems rely on strict validation rules. These rules check whether required fields are present, dates are valid, tax amounts are correct, currencies are consistent, and invoice XML structure follows expected standards.

Today, many validation rules are written as code-heavy XSLT or validator-specific configuration. That makes it hard for compliance, finance operations, and product teams to define or update rules without engineering help.

Build a system where a user can write invoice validation rules in plain English and convert them into deterministic, executable XML validation logic. The system should run the generated rules against XML invoices and return clear pass/fail validation results.

The system should support common rule types such as required field checks, conditional if-then checks, date checks, numeric comparisons, and amount calculation checks.

LLM usage should be minimal. The core solution should use rule templates, parsing, pattern matching, structured intermediate representations, deterministic XSLT generation, validation execution, or a hybrid of these.

# Dataset Requirements

You must generate your own synthetic dataset using the schema below.

Required files and folders:

rules_train.txt: minimum 100 natural language validation rules

rules_test.txt: minimum 30 natural language validation rules

xml_invoices_train/: minimum 300 XML invoice files

xml_invoices_test/: minimum 100 XML invoice files

rule_mappings_train.json: expected structured rule mappings for training rules

validation_labels_train.json: expected validation results for training invoices

# Each natural language rule should include:

rule_id

rule_text

severity

rule_type

expected_error_message

# Supported rule_type values:

required_field

conditional_required_field

date_validation

numeric_comparison

amount_calculation

currency_consistency

tax_category_validation

duplicate_field_check

# Each XML invoice should include realistic invoice fields such as:

invoice_id

issue_date

seller_name

buyer_name

currency_code

taxable_amount

tax_amount

payable_amount

tax_category

tax_exemption_reason

line_items

# Suggested value ranges:

rules per dataset: 100 to 300

XML invoices: 400 to 1,000

line items per invoice: 1 to 50

taxable_amount: 50 to 250,000

tax_amount: 0 to 28% of taxable_amount

payable_amount: taxable_amount + tax_amount, with some intentionally invalid examples

invalid invoice rate: 30% to 50%

The generated dataset should include both valid and invalid invoices. Invalid invoices should cover missing required fields, future issue dates, incorrect tax amounts, mismatched payable amounts, missing exemption reasons, wrong currency codes, malformed XML, and duplicate invoice identifiers.

Final evaluation will use a hidden organizer-generated rule set and XML invoice set with the same structure. Your solution should generalize beyond your own generated rules and invoices.

pint-ae-invoice-invalid-01.xml

pint-ae-invoice-valid-01.xml