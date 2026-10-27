"""Read-only T-002 inventory and integrity scan. Writes only its JSON report."""
from __future__ import annotations
import ast, csv, hashlib, json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "vi_company": "data/raw/vi_company/raw_data.csv",
    "vi_sentiment_train": "data/raw/vi_sentiment/train.csv",
    "vi_sentiment_val": "data/raw/vi_sentiment/val.csv",
    "vi_sentiment_test": "data/raw/vi_sentiment/test.csv",
    "english_sentfin": "data/raw/en_sentfin/SEntFiN.csv",
    "thai_aspect": "data/raw/th_finance/56-1dataset_50.csv",
    "vietnamese_silver": "data/silver/phobert_dataset.csv",
}
EXPECTED = {
    "vi_company": {"Content", "Label"},
    "vi_sentiment_train": {"text", "sentiment"}, "vi_sentiment_val": {"text", "sentiment"},
    "vi_sentiment_test": {"text", "sentiment"}, "english_sentfin": {"Title", "Decisions"},
    "thai_aspect": {"firm", "year", "section", "paragraph", "aspect", "sentiment"},
    "vietnamese_silver": {"ticker", "content", "label", "label_id", "overall_summary",
      "business_score", "leadership_score", "macro_score", "capital_score", "esg_score"},
}
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def scan(name, rel):
    p=ROOT/rel
    if not p.exists(): return {"path":rel,"exists":False}
    with p.open('r',encoding='utf-8-sig',newline='') as f:
        r=csv.DictReader(f); fields=r.fieldnames or []; rows=list(r)
    missing={c:sum(not (x.get(c) or '').strip() for x in rows) for c in fields}
    exact=Counter(tuple((x.get(c) or '').strip() for c in fields) for x in rows)
    result={"path":rel,"exists":True,"bytes":p.stat().st_size,"sha256":digest(p),"rows":len(rows),
      "columns":fields,"required_columns_missing":sorted(EXPECTED[name]-set(fields)),
      "missing_by_column":{k:v for k,v in missing.items() if v},
      "exact_duplicate_rows_beyond_first":sum(n-1 for n in exact.values() if n>1),
      "exact_duplicate_groups":sum(n>1 for n in exact.values()),"samples":[]}
    text_column={'vi_company':'Content','vi_sentiment_train':'text','vi_sentiment_val':'text',
      'vi_sentiment_test':'text','english_sentfin':'Title','thai_aspect':'paragraph',
      'vietnamese_silver':'content'}.get(name)
    if text_column in fields:
        texts=Counter((x.get(text_column) or '').strip() for x in rows)
        result['exact_text_duplicate_rows_beyond_first']=sum(n-1 for n in texts.values() if n>1)
        result['exact_text_duplicate_groups']=sum(n>1 for n in texts.values())
    if name.startswith('vi_sentiment'):
        labels=Counter((x.get('sentiment') or '').strip() for x in rows)
        result['label_distribution']=dict(labels); result['invalid_labels']={k:v for k,v in labels.items() if k not in {'0','1','2'}}
    if name=='vi_company':
        result['label_distribution']=dict(Counter((x.get('Label') or '').strip() for x in rows))
    if name=='english_sentfin':
        sentiment_counts=Counter(); parse_errors=[]; parse_error_count=0; entity_count=0
        for i,x in enumerate(rows):
            try:
                decisions=ast.literal_eval(x.get('Decisions') or '')
                if not isinstance(decisions,dict): raise ValueError('not a dict')
                for target,sent in decisions.items():
                    if not str(target).strip() or str(sent).strip().lower() not in {'negative','neutral','positive'}:
                        raise ValueError('empty target or invalid sentiment')
                    sentiment_counts[str(sent).strip().lower()]+=1; entity_count+=1
            except (ValueError,SyntaxError) as e:
                parse_error_count+=1
                if len(parse_errors)<10: parse_errors.append({'row_1based_data':i+1,'reason':str(e)})
        result['entity_label_rows']=entity_count
        result['sentiment_distribution']=dict(sentiment_counts)
        result['parse_error_sample']=parse_errors
        result['parse_error_count']=parse_error_count
        result['parse_error_sample_is_capped_at']=10
    if name=='thai_aspect':
        result['aspect_distribution']=dict(Counter((x.get('aspect') or '').strip() for x in rows))
        result['sentiment_distribution']=dict(Counter((x.get('sentiment') or '').strip() for x in rows))
        result['invalid_sentiments']={k:v for k,v in result['sentiment_distribution'].items() if k.lower() not in {'negative','neutral','positive'}}
    if name=='vietnamese_silver':
        result['overall_label_distribution']=dict(Counter((x.get('label') or '').strip() for x in rows))
        result['label_id_distribution']=dict(Counter((x.get('label_id') or '').strip() for x in rows))
        result['ticker_count']=len({(x.get('ticker') or '').strip().upper() for x in rows if (x.get('ticker') or '').strip()})
        result['unique_ticker_content_pairs']=len({((x.get('ticker') or '').strip().upper(),(x.get('content') or '').strip()) for x in rows})
        for c in ('business_score','leadership_score','macro_score','capital_score','esg_score'):
            vals=Counter((x.get(c) or '').strip() for x in rows); bad={v:n for v,n in vals.items() if not v or not valid_float(v)}
            result.setdefault('score_invalid',{})[c]=bad
            result.setdefault('score_outside_minus1_plus1',{})[c]={v:n for v,n in vals.items() if valid_float(v) and not -1<=float(v)<=1}
    for i,x in enumerate(rows):
        if len(result['samples'])>=5: break
        if any(not (x.get(c) or '').strip() for c in fields) or (name.startswith('vi_sentiment') and (x.get('sentiment') or '').strip() not in {'0','1','2'}):
            result['samples'].append({"row_1based_data":i+1,"issues":[c for c in fields if not (x.get(c) or '').strip()]})
    return result
def valid_float(v):
    try: float(v); return True
    except (TypeError,ValueError): return False

files={k:scan(k,v) for k,v in FILES.items()}
manifest_path=ROOT/'data/raw/download_manifest.json'
manifest=json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {}
manifest_by_path={str(x.get('local_file','')).replace('\\','/'):x for x in manifest.get('files',[])}
for item in files.values():
    m=manifest_by_path.get(item['path'])
    item['manifest_provenance']=m
    if m and item.get('exists'):
        item['manifest_sha256_matches']=m.get('sha256')==item['sha256']
report={"task":"T-002","mode":"read-only CPU inventory","files":files,
 "gold_files": [str(p.relative_to(ROOT)) for p in (ROOT/'data/gold').rglob('*') if p.is_file()],
 "interpretation":{"vi_company":"DAPT text and noisy company tags; not sentiment labels",
 "vi_sentiment":"general sentiment codes; meaning remains unverified",
 "english_sentfin":"entity-level sentiment, not aspect labels",
 "thai_aspect":"16-category aspect plus sentiment; taxonomy mapping to Vietnamese target aspects remains manual",
 "vietnamese_silver":"LLM pseudo-labels; never Gold; score zero does not establish absence or neutral",
 "gold_test":"No Gold dataset files found under data/gold"},
 "leakage_checks":{"raw_vi_general_split_exact_text_overlap":None,
 "note":"Not computed in this scan; existing processed audit reports zero normalized exact overlaps among selected processed sources. Near/event/translation leakage remains unresolved."},
 "stage_readiness":{"A":"BLOCKED pending DAPT corpus decontamination against sealed Gold test and event/near-duplicate review",
 "B":"PARTIAL: SEntFiN entity labels available, but task/head and lineage/splits need review",
 "C":"PARTIAL: Thai aspect labels available; taxonomy mapping and row granularity must be approved",
 "D":"BLOCKED: no manually adjudicated Vietnamese Gold corpus or sealed split found"}}
out=ROOT/'reports/T-002_DATA_AUDIT.json'; out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(out)
