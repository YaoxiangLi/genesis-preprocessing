from pathlib import Path
import sys
sys.path.insert(0,'tests')
from verify_pipeline import check_reference_failure_diagnostic
case=Path('tests/.runs/regression-hmyddjjn/reference-failures/damaged-index')
assert 'Unverified reference cache' not in (case/'output-run.log').read_text()
check_reference_failure_diagnostic(case,'Unverified reference cache')
try:check_reference_failure_diagnostic(case,'Invented unrelated error')
except AssertionError:pass
else:raise AssertionError('Unrelated failure diagnostic was accepted')
print('PASS: truncated console, complete failed-task evidence, wrong reason rejected')
