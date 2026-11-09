"""Retired preprocessing entry point; do not recreate invalid model labels."""
raise SystemExit(
    'Legacy preprocessing is archived. Run python Code/audit_pipeline.py; '
    'Data/processed/audited contains exploratory data, not calibrated model inputs.'
)
