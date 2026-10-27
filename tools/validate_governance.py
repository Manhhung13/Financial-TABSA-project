"""Offline-only integrity checks for Codex governance pack (stdlib only)."""
from pathlib import Path
import re
import sys
try:
    import tomllib
except ImportError:
    print('Requires Python 3.11+ for TOML validation.'); sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = ['AGENTS.md','state/CURRENT.md','state/HANDOFF.md','docs/PROJECT_BRIEF.md','docs/DOMAIN_RULES.md','docs/DATA_CONTRACT.md','docs/ML_DESIGN.md','docs/MODEL_ROUTING.md','plans/MASTER_PLAN.md','tasks/INDEX.md','.codex/config.toml']
errs=[]
for path in REQUIRED:
    if not (ROOT/path).is_file(): errs.append('Missing required: '+path)
for path in (ROOT/'.codex').rglob('*.toml'):
    try:tomllib.loads(path.read_text('utf-8'))
    except Exception as e:errs.append(f'Bad TOML {path.relative_to(ROOT)}: {e}')
for path in (ROOT/'tasks').glob('T-*.md'):
    data=path.read_text('utf-8');
    if not re.match(r'# T-\d{3}: ',data):errs.append('Bad task title: '+path.name)
    for label in ['Status:','Owner:','Depends on:','Context (read ONLY):','Acceptance criteria','Minimum validation']:
        if label not in data:errs.append(f'{path.name} missing {label}')
if len(list((ROOT/'tasks').glob('T-*.md'))) != 12:errs.append('Expected 12 registered tasks after T-012 Data Readiness')
for s in (ROOT/'.agents/skills').glob('*/SKILL.md'):
    txt=s.read_text('utf-8')
    if not txt.startswith('---\nname:'): errs.append('Bad skill frontmatter: '+str(s))
print('Governance paths:',len(list(ROOT.rglob('*'))))
if errs:
    for e in errs: print('ERROR:',e)
    sys.exit(1)
print('VALIDATION OK: governance structure, TOML and task schema checks passed.')
