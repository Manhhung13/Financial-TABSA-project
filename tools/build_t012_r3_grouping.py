"""Read-only, deterministic T-012 R3 document and grouping audit."""
import csv, hashlib, json, re, unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
 ("VI_COMPANY","data/raw/vi_company/raw_data.csv","Content","Label"),
 ("VI_SENT_TRAIN","data/raw/vi_sentiment/train.csv","text","sentiment"),
 ("VI_SENT_VAL","data/raw/vi_sentiment/val.csv","text","sentiment"),
 ("VI_SENT_TEST","data/raw/vi_sentiment/test.csv","text","sentiment"),
 ("EN_SENTFIN","data/raw/en_sentfin/SEntFiN.csv","Title","Decisions"),
 ("TH_ASPECT","data/raw/th_finance/56-1dataset_50.csv","paragraph","aspect"),
 ("VI_SILVER","data/silver/phobert_dataset.csv","content","ticker"),
]
def sha(s): return hashlib.sha256(s.encode("utf-8")).hexdigest()
def norm(s):
 s=unicodedata.normalize("NFKC",s or "").casefold()
 s="".join(c for c in s if not unicodedata.category(c).startswith("P"))
 return " ".join(s.split())
def docid(source, rowhash): return "doc_"+sha(source+":"+rowhash)[:20]
rows=[]; filemeta=[]
for ds,rel,textcol,meta in SOURCES:
 p=ROOT/rel; raw=p.read_bytes(); filehash=hashlib.sha256(raw).hexdigest()
 with p.open(encoding="utf-8-sig",newline="") as f:
  reader=csv.DictReader(f)
  for n,r in enumerate(reader,1):
   text=r.get(textcol) or ""; nh=norm(text); exact=sha(text); normalized=sha(nh)
   # Row-level identity preserves distinct targets/aspects and labels.
   row_payload=json.dumps([ds,n,text,r.get(meta)],ensure_ascii=False,separators=(",",":"))
   rows.append({"source_dataset":ds,"source_path":rel,"source_file_sha256":filehash,"source_row":n,
    "source_article_id":r.get("S No."),"company_raw":r.get("Label") or r.get("ticker") or r.get("firm"),
    "published_date":r.get("year"),"aspect_raw":r.get("aspect"),"label_raw":r.get("sentiment") or r.get("Decisions") or r.get("label"),
    "document_id":docid(ds,sha(row_payload)),"row_sha256":sha(row_payload),"raw_text_sha256":exact,
    "normalized_text_sha256":normalized,"normalized_text":nh,"text":text})
 filemeta.append({"dataset":ds,"path":rel,"sha256":filehash,"rows":n})
# Exact text groups, by raw and conservative normalized hash.
rawgroups=defaultdict(list); ngroups=defaultdict(list)
for x in rows: rawgroups[(x['source_dataset'],x['raw_text_sha256'])].append(x); ngroups[(x['source_dataset'],x['normalized_text_sha256'])].append(x)
exact=[]
for (ds,h),g in rawgroups.items():
 if len(g)>1: exact.append({"match_type":"exact_raw_text","source_dataset":ds,"text_sha256":h,"document_ids":[x['document_id'] for x in g],"source_rows":[x['source_row'] for x in g],"row_count":len(g),"disposition":"preserve_all_rows"})
for (ds,h),g in ngroups.items():
 if len(g)>1 and len({x['raw_text_sha256'] for x in g})>1: exact.append({"match_type":"exact_normalized_text","source_dataset":ds,"normalized_text_sha256":h,"document_ids":[x['document_id'] for x in g],"source_rows":[x['source_row'] for x in g],"row_count":len(g),"disposition":"review_normalization_collision"})
# Cross-source exact text is separately exposed; identity labels never collapse rows.
for label,key in (("exact_raw_text_cross_source","raw_text_sha256"),("exact_normalized_text_cross_source","normalized_text_sha256")):
 groups=defaultdict(list)
 for x in rows: groups[x[key]].append(x)
 for h,g in groups.items():
  if len({x['source_dataset'] for x in g})>1:
   exact.append({"match_type":label,"text_sha256":h,"datasets":sorted({x['source_dataset'] for x in g}),"document_ids":[x['document_id'] for x in g],"source_rows":[x['source_row'] for x in g],"row_count":len(g),"disposition":"review_cross_source_lineage; preserve all rows"})
# CPU-efficient candidates: length-qualified shared rare word shingles, capped posting lists.
eligible=[x for x in rows if len(x['normalized_text'])>=80]
post=defaultdict(list)
for i,x in enumerate(eligible):
 toks=set(re.findall(r"[^\W_]+",x['normalized_text'],flags=re.UNICODE))
 x['_tokens']=toks
 for t in toks:
  if len(t)>=4: post[t].append(i)
cands=set()
for i,x in enumerate(eligible):
 shared=set()
 for t in x['_tokens']:
  p=post[t]
  if len(p)<=80: shared.update(j for j in p if j>i)
 for j in shared:
  y=eligible[j]
  if abs(len(x['normalized_text'])-len(y['normalized_text']))/max(len(x['normalized_text']),len(y['normalized_text']))<=.15: cands.add((i,j))
near=[]
for i,j in sorted(cands):
 a,b=eligible[i],eligible[j]; inter=len(a['_tokens']&b['_tokens']); union=len(a['_tokens']|b['_tokens']); jac=inter/union if union else 0
 if jac>=.88 and a['normalized_text_sha256']!=b['normalized_text_sha256']:
  near.append({"candidate_id":"near_"+sha(a['document_id']+b['document_id'])[:16],"left_document_id":a['document_id'],"right_document_id":b['document_id'],"left_dataset":a['source_dataset'],"right_dataset":b['source_dataset'],"left_row":a['source_row'],"right_row":b['source_row'],"token_jaccard":round(jac,5),"left_text_sha256":a['raw_text_sha256'],"right_text_sha256":b['raw_text_sha256'],"review_status":"needs_human_review","merge_status":"not_merged","risk":"shared boilerplate or same issuer topic can cause false match"})
# Queue unresolved lineage inventories, not inferred shared-event pairs.
events=[]
for x in rows:
 if not x['source_article_id'] or not x['published_date']:
  events.append({"document_id":x['document_id'],"source_dataset":x['source_dataset'],"source_article_id":x['source_article_id'],"company_raw":x['company_raw'],"published_date":x['published_date'],"unresolved_fields":[k for k,v in (("source_article_id",x['source_article_id']),("published_date",x['published_date'])) if not v],"review_status":"unresolved_lineage","event_group_id":None,"merge_status":"not_merged"})
ledger=[]
for x in rows:
 ledger.append({k:v for k,v in x.items() if k not in ('text','normalized_text','_tokens')})
out=ROOT/'reports'
(out/'T-012_R3_grouping_ledger.json').write_text(json.dumps({"task":"T-012 R3","version":"1.0.0","policy":"Deterministic row/document IDs; raw and normalized text hashes; no automatic merge; preserve all labels/targets/aspects.","sources":filemeta,"records":ledger},ensure_ascii=False,indent=2)+"\n",encoding='utf-8')
(out/'T-012_R3_exact_duplicate_groups.json').write_text(json.dumps(exact,ensure_ascii=False,indent=2)+"\n",encoding='utf-8')
(out/'T-012_R3_near_duplicate_review_queue.json').write_text(json.dumps(near,ensure_ascii=False,indent=2)+"\n",encoding='utf-8')
(out/'T-012_R3_event_review_queue.json').write_text(json.dumps(events,ensure_ascii=False,indent=2)+"\n",encoding='utf-8')
print(json.dumps({"rows":len(rows),"files":filemeta,"exact_groups":len(exact),"near_candidates":len(near),"event_candidates":len(events),"candidate_pairs_checked":len(cands)},ensure_ascii=False))
