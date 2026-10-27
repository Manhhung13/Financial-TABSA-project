"""Read-only, conservative target-tag audit for T-002."""
from __future__ import annotations
import ast, csv, json, re, unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCES={
 'vi_company':('data/raw/vi_company/raw_data.csv','Label','Content'),
 'vi_silver':('data/silver/phobert_dataset.csv','ticker','content'),
 'sentfin':('data/raw/en_sentfin/SEntFiN.csv','Decisions','Title'),
 'thai_firm':('data/raw/th_finance/56-1dataset_50.csv','firm','paragraph'),
}
SUSPICIOUS_TERMS={'CEO','CPI','EPS','GDP','MOU','NAV','NIM','ROA','ROE'}
TICKER_RE=re.compile(r'^[A-Z0-9]{3}$')
def norm(v):
    return ' '.join(unicodedata.normalize('NFKC',str(v or '')).split()).upper()
def read_csv(p):
    with (ROOT/p).open(encoding='utf-8-sig',newline='') as f:
        r=csv.DictReader(f); fields=r.fieldnames or []; rows=list(r)
    return fields,rows
def tags_for_row(name,raw):
    if name!='sentfin': return [raw]
    try:
        d=ast.literal_eval(raw)
        if not isinstance(d,dict): raise ValueError('Decisions is not a dict')
        return [str(k) for k in d]
    except (ValueError,SyntaxError): return None
def reason_codes(raw, ticker_format=True):
    n=norm(raw); out=[]
    if not n: out.append(('confirmed_error','empty_tag'))
    if any(unicodedata.category(c)=='Cc' for c in str(raw)): out.append(('confirmed_error','control_character'))
    if len(n)>64: out.append(('confirmed_error','tag_over_64_characters'))
    if any(ch in n for ch in ',;|'): out.append(('heuristic_warning','contains_multi_value_delimiter'))
    if ticker_format and n and not TICKER_RE.fullmatch(n): out.append(('heuristic_warning','not_conventional_three_character_ticker_format'))
    if n in SUSPICIOUS_TERMS: out.append(('heuristic_warning','financial_term_or_role_acronym_not_verified_as_ticker'))
    return out
def process(name,spec):
    rel,tag_col,text_col=spec; fields,rows=read_csv(rel)
    if tag_col not in fields or text_col not in fields:
        return {'path':rel,'schema_columns':fields,'error':'expected target/text fields absent'}
    raw_freq=Counter(); normalized=defaultdict(Counter); reason_stats=defaultdict(lambda:{'rows':0,'affected_rows':set(),'distinct_raw_tags':set()})
    examples_by_reason=defaultdict(list); parse_errors=[]; empty_rows=0; text_absent_rows=0; ambiguous_rows=set()
    all_tags=[]
    for i,row in enumerate(rows,1):
        raw_value=row.get(tag_col) or ''; text=row.get(text_col) or ''
        tag_list=tags_for_row(name,raw_value)
        if tag_list is None:
            parse_errors.append(i)
            if len(examples_by_reason['unparseable_target_dictionary'])<8: examples_by_reason['unparseable_target_dictionary'].append({'data_row':i,'raw_tag':raw_value[:180],'classification':'confirmed_error','reason':'unparseable_target_dictionary','evidence_excerpt':text[:200]})
            continue
        if name!='sentfin' and not raw_value.strip(): empty_rows+=1
        row_codes=set()
        for raw in tag_list:
            raw=str(raw); n=norm(raw); raw_freq[raw]+=1; normalized[n][raw]+=1; all_tags.append(raw)
            codes=reason_codes(raw,ticker_format=name!='sentfin')
            for cls,code in codes:
                st=reason_stats[(cls,code)]; st['rows']+=1; st['affected_rows'].add(i); st['distinct_raw_tags'].add(raw); row_codes.add((cls,code))
            if any(cls=='heuristic_warning' and code in {'contains_multi_value_delimiter','financial_term_or_role_acronym_not_verified_as_ticker'} for cls,code in codes): ambiguous_rows.add(i)
            if text and n and not re.search(r'(?<![A-Z0-9])'+re.escape(n)+r'(?![A-Z0-9])',norm(text)):
                text_absent_rows+=1
                st=reason_stats[('heuristic_warning','tag_not_found_verbatim_in_associated_text')];st['rows']+=1;st['affected_rows'].add(i);st['distinct_raw_tags'].add(raw)
                if len(examples_by_reason['tag_not_found_verbatim_in_associated_text'])<8: examples_by_reason['tag_not_found_verbatim_in_associated_text'].append({'data_row':i,'raw_tag':raw[:180],'normalized_tag':n,'classification':'heuristic_warning','reason':'tag_not_found_verbatim_in_associated_text_identity_unverified','evidence_excerpt':text[:200]})
            for cls,code in codes:
                if len(examples_by_reason[code])<8: examples_by_reason[code].append({'data_row':i,'raw_tag':raw[:180],'normalized_tag':n,'classification':cls,'reason':code,'evidence_excerpt':text[:200]})
    collisions={n:dict(sorted(v.items())) for n,v in normalized.items() if len(v)>1}
    freq=dict(sorted(raw_freq.items()))
    confirmed_bad_rows=set().union(*(v['affected_rows'] for (cls,_),v in reason_stats.items() if cls=='confirmed_error')) if reason_stats else set()
    return {'path':rel,'schema_columns':fields,'row_count':len(rows),'tag_field':tag_col,'text_field':text_col,
      'target_values_parsed':len(all_tags),'parse_error_rows':len(parse_errors) if name=='sentfin' else None,
      'parse_error_row_numbers':parse_errors[:40] if name=='sentfin' else [],
      'empty_tag_rows':empty_rows if name!='sentfin' else None,
      'distinct_raw_tags':len(raw_freq),'distinct_normalized_tags':len(normalized),
      'unresolved_mappings_without_trusted_reference':len(normalized),
      'confirmed_invalid_tag_rows':len(confirmed_bad_rows),
      'raw_tag_frequencies':freq,
      'normalized_tag_groups':{n:dict(sorted(v.items())) for n,v in sorted(normalized.items())},
      'normalization_collision_count':len(collisions),'normalization_collisions':collisions,
      'heuristic_nonconventional_format_distinct':sum(not TICKER_RE.fullmatch(n) for n in normalized) if name!='sentfin' else None,
      'suspicious_acronym_distinct':sum(n in SUSPICIOUS_TERMS for n in normalized),
      'rows_with_ambiguous_or_suspicious_tag':len(ambiguous_rows),
      'rows_tag_absent_verbatim_from_context':text_absent_rows,
      'review_reason_stats':{f'{c}:{r}':{'affected_tag_occurrences':v['rows'],'affected_rows':len(v['affected_rows']),'distinct_raw_tags':len(v['distinct_raw_tags']),'examples':sorted(v['distinct_raw_tags'])[:12]} for (c,r),v in reason_stats.items()},
      'representative_review_candidates':[x for group in examples_by_reason.values() for x in group][:40]}

results={n:process(n,s) for n,s in SOURCES.items()}
cross={}
for a,b in [('vi_company','vi_silver'),('vi_company','sentfin'),('vi_silver','sentfin')]:
    left=set(results[a].get('normalized_tag_groups',{}));right=set(results[b].get('normalized_tag_groups',{}));shared=left&right
    cross[a+'__'+b]={'shared_normalized_strings_count':len(shared),'examples':sorted(shared)[:30],
      'interpretation':'string overlap only; no authoritative ticker-to-company reference exists'}
report={'task':'T-002 target alias audit','read_only':True,
 'normalization':{'unicode':'NFKC','whitespace':'trim and collapse runs','case':'uppercase','punctuation':'preserved; no token splitting or suffix stripping','ticker_format_heuristic':'exactly 3 ASCII uppercase letters/digits; warning only'},
 'trusted_reference_check':{'available':False,'checked_existing_project_inventories':['data/raw','data/processed','data/silver','docs'],'finding':'No authoritative issuer/ticker master or verified alias table found. Source tags are assertions, not independent verification references.'},
 'sources':results,'cross_source':cross,
 'limitations':['Text absence is a heuristic; company may be named without its ticker.','Non-three-character formats are warnings, not confirmed errors.','No ticker/company mapping or source tag was corrected.','Candidate examples are capped at 40 per source; complete distinct tag frequencies and normalized groups are included.']}
out=ROOT/'reports/T-002_TARGET_ALIAS_AUDIT.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(out)
