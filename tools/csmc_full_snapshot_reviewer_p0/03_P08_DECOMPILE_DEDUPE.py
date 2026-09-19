from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

OWNER_RE = re.compile(r'(?:^|_)(1[0-9a-fA-F]{8,15})(?:_|\\.)')
FUN_RE = re.compile(r'\\bFUN_(1[0-9a-fA-F]{8,15})\\b')

REVIEW_TERMS = {
    'consumer': ['Canvas3DModelLoader','ModelData','ModelData3D','Layer3DModelData','deserialize','reader','payload','factory','vtable','virtual'],
    'stream': ['read','stream','buffer','memcpy','copy','cursor','offset'],
    'bridge': ['glBufferSubData','glBufferData','OpenGL','vertex buffer','upload','VBO'],
    'transform': ['bone','weight','skin','skeleton','matrix','transform','quaternion'],
}

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--input', action='append', default=[])
    return ap.parse_args()

def safe_text(path: Path) -> str:
    try:
        data = path.read_bytes()
    except Exception:
        return ''
    for enc in ('utf-8','utf-8-sig','utf-16','cp932','latin1'):
        try:
            return data.decode(enc)
        except Exception:
            pass
    return ''

def owner_from_rel(rel: str) -> str:
    low = rel.lower()
    if 'decompile' not in low or not low.endswith('.txt'):
        return ''
    m = OWNER_RE.search(Path(rel).name)
    return ('0x' + m.group(1).lower()) if m else ''

def read_tsv(path: Path):
    if not path.exists():
        return []
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))

def write_tsv(path: Path, rows, fields):
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter='\t', extrasaction='ignore')
        w.writeheader()
        for row in rows:
            w.writerow(row)

def build_manifest(inputs):
    rows=[]
    by=defaultdict(list)
    seen=set()
    for label, root in inputs:
        if not root.exists():
            continue
        for p in root.rglob('*'):
            if not p.is_file():
                continue
            rel=str(p.relative_to(root))
            owner=owner_from_rel(rel)
            if not owner:
                continue
            key=(label,rel,owner)
            if key in seen:
                continue
            seen.add(key)
            try:
                b=p.read_bytes()
                size=len(b)
                sha=hashlib.sha256(b).hexdigest()
            except Exception:
                size=0; sha=''
            row={'rva':owner,'snapshot':label,'file':rel,'bytes':size,'sha256':sha}
            rows.append(row); by[owner].append(row)
    rows.sort(key=lambda x:(x['rva'],x['snapshot'],x['file']))
    return rows,by

def score_old_c(text: str):
    low=text.lower()
    c=Counter()
    for cat,terms in REVIEW_TERMS.items():
        for term in terms:
            c[cat]+=low.count(term.lower())
    return c

def main():
    args=parse_args()
    out=Path(args.out)
    inputs=[]
    for item in args.input:
        if '=' not in item:
            raise SystemExit('bad --input: '+item)
        label,p=item.split('=',1)
        inputs.append((label.strip(),Path(p)))
    roots={label:root for label,root in inputs}

    manifest,by=build_manifest(inputs)
    write_tsv(out/'decompile_manifest.tsv', manifest, ['rva','snapshot','file','bytes','sha256'])

    candidates=read_tsv(out/'consumer_candidates.tsv')
    deduped=[]
    for r in candidates:
        rva=r.get('rva','').lower()
        existing=by.get(rva,[])
        r['candidate_status']='ALREADY_DECOMPILED' if existing else 'NEW_DIRECT_TARGET'
        r['decompile_count']=str(len(existing))
        r['decompile_paths']=' | '.join(x['snapshot']+':'+x['file'] for x in existing[:12])
        deduped.append(r)

    base_fields=list(candidates[0].keys()) if candidates else []
    for extra in ['candidate_status','decompile_count','decompile_paths']:
        if extra not in base_fields:
            base_fields.append(extra)
    write_tsv(out/'consumer_candidates_p08.tsv', deduped, base_fields)

    existing_rows=[]
    review_md=['# CSMC P0.8 EXISTING DECOMPILE RE-READ','',
               'These functions already have snapshot decompiles. Re-read them; do not rerun Ghidra.','']
    for r in deduped:
        if r['candidate_status']!='ALREADY_DECOMPILED':
            continue
        rva=r['rva'].lower()
        counts=Counter()
        file_labels=[]
        body_parts=[]
        for m in by.get(rva,[]):
            root=roots.get(m['snapshot'])
            if root is None:
                continue
            p=root/m['file']
            text=safe_text(p)
            counts.update(score_old_c(text))
            file_labels.append(m['snapshot']+':'+m['file'])
            if len(body_parts)<3 and text:
                body=text.strip()
                if len(body)>12000:
                    body=body[:12000]+'\n[TRUNCATED]\n'
                body_parts.append('FILE '+m['snapshot']+' :: '+m['file']+'\n'+body)
        row={
            'rva':rva,
            'aggregate_score':r.get('aggregate_score',''),
            'consumer_score':r.get('consumer_score',''),
            'bridge_score':r.get('bridge_score',''),
            'transform_score':r.get('transform_score',''),
            'decompile_file_count':len(by.get(rva,[])),
            'consumer_hits':counts['consumer'],
            'stream_hits':counts['stream'],
            'bridge_hits':counts['bridge'],
            'transform_hits':counts['transform'],
            'decompile_files':' | '.join(file_labels[:12]),
        }
        existing_rows.append(row)
        if len(review_md)<220:
            review_md += ['', '## '+rva,
                          'status=ALREADY_DECOMPILED',
                          'current_term_hits consumer=%s stream=%s bridge=%s transform=%s' % (counts['consumer'],counts['stream'],counts['bridge'],counts['transform']),
                          '', '\n\n'.join(body_parts)]

    write_tsv(out/'existing_decompile_review.tsv', existing_rows,
              ['rva','aggregate_score','consumer_score','bridge_score','transform_score','decompile_file_count','consumer_hits','stream_hits','bridge_hits','transform_hits','decompile_files'])
    (out/'EXISTING_DECOMPILE_REVIEW.md').write_text('\n'.join(review_md)+'\n',encoding='utf-8')

    new_direct=[r for r in deduped if r['candidate_status']=='NEW_DIRECT_TARGET']
    def ok(r):
        try:
            agg=int(float(r.get('aggregate_score','0') or 0))
            cons=int(float(r.get('consumer_score','0') or 0))
            bridge=int(float(r.get('bridge_score','0') or 0))
            trans=int(float(r.get('transform_score','0') or 0))
            code=int(float(r.get('code_evidence_count','0') or 0))
        except Exception:
            return False
        return agg>=12 and code>=1 and (cons>=1 or bridge>=1 or trans>=2)

    targets=[r for r in new_direct if ok(r)][:8]
    with (out/'ghidra_targets.txt').open('w',encoding='utf-8') as f:
        f.write('# CSMC FULL SNAPSHOT REVIEWER P0.8\n')
        f.write('# reviewer_build=P0.8_decompile_dedupe\n')
        f.write('# NEW_DIRECT_TARGET only. Existing decompiles are excluded.\n')
        f.write('# Do not broad-scan around these targets.\n\n')
        for i,r in enumerate(targets,1):
            f.write('%d\t%s\tscore=%s\tevidence=%s\tconsumer=%s\tbridge=%s\ttransform=%s\n' % (
                i,r.get('rva',''),r.get('aggregate_score',''),r.get('evidence_count',''),
                r.get('consumer_score',''),r.get('bridge_score',''),r.get('transform_score','')))

    top=deduped[:20]
    summary=[
        '# CSMC FULL SNAPSHOT REVIEWER P0.8 — SUMMARY','',
        'P0.8 adds decompile-manifest dedupe on top of the P0.7 direct-evidence review.','',
        '- Existing decompile manifest entries: **%d**' % len(manifest),
        '- Candidate rows: **%d**' % len(deduped),
        '- ALREADY_DECOMPILED candidates: **%d**' % sum(1 for r in deduped if r['candidate_status']=='ALREADY_DECOMPILED'),
        '- NEW_DIRECT_TARGET candidates: **%d**' % len(new_direct),
        '- Ghidra targets after dedupe: **%d**' % len(targets),'',
        '## Top candidates after dedupe',''
    ]
    for r in top:
        summary.append('- %s — score=%s, status=%s, decompile_count=%s' % (r.get('rva',''),r.get('aggregate_score',''),r.get('candidate_status',''),r.get('decompile_count','0')))
    summary += ['', '## Next action','',
                '- ALREADY_DECOMPILED: re-read EXISTING_DECOMPILE_REVIEW.md; do not rerun Ghidra.',
                '- NEW_DIRECT_TARGET: only these may enter 10_RUN_GHIDRA_TARGETS.bat.',
                '- Consumer research next branch: known loader vtables / indirect dispatch, not another generic string-XREF loop.']
    (out/'SUMMARY_P08.md').write_text('\n'.join(summary)+'\n',encoding='utf-8')

    packet=['# CSMC P0.8 CHATGPT PACKET','', '\n'.join(summary), '', '--- GHIDRA NEW DIRECT TARGETS ---', (out/'ghidra_targets.txt').read_text(encoding='utf-8'), '', '--- EXISTING DECOMPILE REVIEW TABLE ---']
    p=out/'existing_decompile_review.tsv'
    packet.append(p.read_text(encoding='utf-8',errors='replace')[:200000] if p.exists() else '[missing]')
    packet += ['', '--- CANDIDATE DEDUPE ---']
    p=out/'consumer_candidates_p08.tsv'
    packet.append(p.read_text(encoding='utf-8',errors='replace')[:250000] if p.exists() else '[missing]')
    (out/'CHATGPT_PACKET_P08.md').write_text('\n'.join(packet)+'\n',encoding='utf-8')

    print('P08_DECOMPILE_MANIFEST='+str(len(manifest)))
    print('P08_ALREADY_DECOMPILED='+str(sum(1 for r in deduped if r['candidate_status']=='ALREADY_DECOMPILED')))
    print('P08_NEW_DIRECT_TARGETS='+str(len(new_direct)))
    print('P08_GHIDRA_TARGETS='+str(len(targets)))
    print('P08_PACKET='+str(out/'CHATGPT_PACKET_P08.md'))

if __name__=='__main__':
    main()