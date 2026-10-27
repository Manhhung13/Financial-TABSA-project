"""Print minimal task context; no network, files remain authoritative."""
from pathlib import Path
import argparse,re,sys
r=Path(__file__).resolve().parent.parent
ap=argparse.ArgumentParser();ap.add_argument('task_id',help='T-001 etc');a=ap.parse_args()
if not re.fullmatch(r'T-\d{3}',a.task_id):sys.exit('Expected T-001 format')
items=list((r/'tasks').glob(a.task_id+'-*.md'))
if len(items)!=1:sys.exit('Task not found or ambiguous')
print('=== CURRENT ===\n'+(r/'state/CURRENT.md').read_text('utf-8'))
print('=== TASK ===\n'+items[0].read_text('utf-8'))
print('=== READ ONLY LINKS FROM CONTEXT LINE; DO NOT AUTO-DUMP WHOLE DOC TREE ===')
