#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sqlite3, struct
from pathlib import Path

FIXTURES = {
    "F03": "CSMC_F03_CUBE.csmc",
    "F06": "CSMC_F06_CUBE_MAT2.csmc",
    "F07": "CSMC_F07_TWO_CUBES.csmc",
    "R03": "CSMC_R03_CUBE_B2_W100.csmc",
    "R04": "CSMC_R04_CUBE_B2_SPLIT.csmc",
    "V01": "CSMC_V01_VROID_BODY_BASE.csmc",
}
RENDER_PARTS = {"F03": 1, "F06": 2, "F07": 2, "R03": 1, "R04": 1, "V01": 8}
# Public-safe canonical phase-core starts derived from prior validated structural IR.
BOUNDARY_QWORDS = {"F06": 762, "F07": 774, "R03": 473, "R04": 480, "V01": 533940}
WINDOW_BYTES = 2048
CADENCE_QWORDS = 307
CADENCE_BYTES = 2456

def sha256_file(p: Path) -> str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20), b""):
            h.update(chunk)
    return h.hexdigest()

def character_blob(p: Path) -> bytes:
    con=sqlite3.connect(str(p))
    try:
        row=con.execute("select character from character limit 1").fetchone()
    finally:
        con.close()
    if not row or not isinstance(row[0], (bytes, bytearray)):
        raise RuntimeError(f"missing character BLOB: {p}")
    return bytes(row[0])

def payload_info(blob: bytes):
    if len(blob) < 65:
        raise RuntimeError("short DATA2 blob")
    inner_version=struct.unpack_from("<I", blob, 53)[0]
    logical=struct.unpack_from("<I", blob, 57)[0]
    stored=struct.unpack_from("<I", blob, 61)[0]
    if inner_version != 2:
        raise RuntimeError("unexpected inner version")
    if stored != ((logical + 7)//8)*8 + 8:
        raise RuntimeError("framing rule mismatch")
    payload=blob[65:65+stored]
    if len(payload) != stored:
        raise RuntimeError("truncated payload")
    return logical, stored, payload

def qwords(payload: bytes):
    if len(payload)%8:
        raise RuntimeError("stored payload not qword aligned")
    return [payload[i:i+8] for i in range(0,len(payload),8)]

def window_hashes(qs, L):
    out={}
    for i in range(len(qs)-L+1):
        digest=hashlib.sha256(b"".join(qs[i:i+L])).digest()
        out.setdefault(digest, []).append(i)
    return out

def triple_common_block(a,b,c,L=CADENCE_QWORDS):
    hs=[window_hashes(x,L) for x in (a,b,c)]
    common=set(hs[0]) & set(hs[1]) & set(hs[2])
    triples=[]
    for h in common:
        for i in hs[0][h]:
            for j in hs[1][h]:
                for k in hs[2][h]:
                    # SHA-256 is only a locator; verify raw in-memory equality before use.
                    if a[i:i+L] == b[j:j+L] == c[k:k+L]:
                        triples.append((i,j,k))
    triples.sort()
    best=None
    if triples:
        start=prev=triples[0]
        count=1
        for t in triples[1:]:
            if t==(prev[0]+1,prev[1]+1,prev[2]+1):
                count+=1
            else:
                cand=(count,start,prev)
                if best is None or cand[0]>best[0]:
                    best=cand
                start=t; count=1
            prev=t
        cand=(count,start,prev)
        if best is None or cand[0]>best[0]:
            best=cand
    if best is None:
        return None
    run_count,start,last=best
    exact_len=L+run_count-1
    return {"start_qwords":{"F03":start[0],"F06":start[1],"F07":start[2]},
            "window_run_count":run_count,
            "exact_length_qwords":exact_len,
            "exact_length_bytes":exact_len*8}

def scalar_value(payload: bytes, start: int, width: int, endian: str) -> int|None:
    if start<0 or start+width>len(payload):
        return None
    return int.from_bytes(payload[start:start+width], endian)

def scalar_hits(payloads):
    phase_sets={
        "PHASE1":["F06","F07","R03"],
        "PHASE3":["R04","V01"],
    }
    hits=[]
    evaluated=0
    for target_kind in ("render_part_count","cadence_count"):
        for phase,names in phase_sets.items():
            for width in (1,2,4):
                endians=("little",) if width==1 else ("little","big")
                for endian in endians:
                    for d in range(width,WINDOW_BYTES+1):
                        evaluated+=1
                        ok=True
                        for n in names:
                            target=RENDER_PARTS[n] + (2 if target_kind=="cadence_count" else 0)
                            pos=BOUNDARY_QWORDS[n]*8-d
                            if scalar_value(payloads[n],pos,width,endian)!=target:
                                ok=False
                                break
                        if ok:
                            hits.append({"target_kind":target_kind,"phase":phase,"width":width,
                                         "endianness":endian,"boundary_relative_start":-d})
    return evaluated,hits

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("fixture_dir")
    ap.add_argument("--out", required=True)
    ap.add_argument("--corpus-sha256", default=None)
    args=ap.parse_args()
    root=Path(args.fixture_dir)
    infos={}
    payloads={}
    for key,fn in FIXTURES.items():
        p=root/fn
        blob=character_blob(p)
        logical,stored,payload=payload_info(blob)
        payloads[key]=payload
        infos[key]={"file_sha256":sha256_file(p),"logical_length":logical,"stored_length":stored,
                    "logical_mod8":logical%8,"payload_qwords":stored//8}
    common=triple_common_block(*(qwords(payloads[k]) for k in ("F03","F06","F07")))
    if common is None:
        raise RuntimeError("no 307-qword triple-common locator")
    starts=common["start_qwords"]
    L=common["exact_length_qwords"]
    ends={k:starts[k]+L for k in starts}
    pre_shift={"F06_minus_F03_bytes":(starts["F06"]-starts["F03"])*8,
               "F07_minus_F03_bytes":(starts["F07"]-starts["F03"])*8,
               "F07_minus_F06_bytes":(starts["F07"]-starts["F06"])*8}
    logical_delta={"F06_minus_F03":infos["F06"]["logical_length"]-infos["F03"]["logical_length"],
                   "F07_minus_F03":infos["F07"]["logical_length"]-infos["F03"]["logical_length"],
                   "F07_minus_F06":infos["F07"]["logical_length"]-infos["F06"]["logical_length"]}
    post_logical={"F06_minus_F03_bytes":logical_delta["F06_minus_F03"]-pre_shift["F06_minus_F03_bytes"],
                  "F07_minus_F03_bytes":logical_delta["F07_minus_F03"]-pre_shift["F07_minus_F03_bytes"]}
    evaluated,hits=scalar_hits(payloads)
    block=payloads["F03"][starts["F03"]*8:ends["F03"]*8]
    vpos=payloads["V01"].find(block)
    out={
        "schema_version":"csmc_render_part_residual_localization_v0_1",
        "source_corpus_sha256":args.corpus_sha256,
        "pipeline_stage":"STRUCTURAL_ONLY",
        "candidate_semantic":"TAIL_2456_RENDER_PART_CARDINALITY_CANDIDATE",
        "confidence_before":"LEVEL_4_CANDIDATE",
        "confidence_after":"LEVEL_4_CANDIDATE_REFINED_NOT_PROMOTED",
        "raw_bytes_embedded":False,
        "semantic_promotion":False,
        "blender_emit":False,
        "cadence_bytes":CADENCE_BYTES,
        "cadence_qwords":CADENCE_QWORDS,
        "triple_common_locator":common,
        "triple_common_v01_occurrence_qword":(vpos//8 if vpos>=0 and vpos%8==0 else None),
        "pre_common_block_shifts":pre_shift,
        "logical_length_deltas_bytes":logical_delta,
        "post_common_block_logical_growth_bytes":post_logical,
        "common_post_growth_decomposition":{
            "F06_minus_F03": {"cadence_bytes":CADENCE_BYTES,
                              "other_bytes":post_logical["F06_minus_F03_bytes"]-CADENCE_BYTES},
            "F07_minus_F03": {"cadence_bytes":CADENCE_BYTES,
                              "other_bytes":post_logical["F07_minus_F03_bytes"]-CADENCE_BYTES},
        },
        "phase1_exact_suffix_alignment":{
            "F06_start_qword":445,"F07_start_qword":457,"length_qwords":2118,
            "variable_prefix_delta_bytes":(457-445)*8,
        },
        "boundary_relative_scalar_negative_control":{
            "window_bytes":WINDOW_BYTES,
            "targets":["render_part_count","cadence_count"],
            "widths":[1,2,4],
            "endianness":["little","big"],
            "phase_sets":{"PHASE1":["F06","F07","R03"],"PHASE3":["R04","V01"]},
            "canonical_boundary_qwords":BOUNDARY_QWORDS,
            "candidate_configurations_evaluated":evaluated,
            "hard_pass_count":len(hits),
            "hits":hits,
            "scope_note":"Rejects only direct raw scalar equality at one shared boundary-relative offset inside the last 2048 bytes before the validated phase-core boundary."
        },
        "fixtures":infos,
    }
    Path(args.out).write_text(json.dumps(out,indent=2,sort_keys=True))
    print(json.dumps({
        "exact_length_qwords":common["exact_length_qwords"],
        "starts":starts,
        "v01_qword":out["triple_common_v01_occurrence_qword"],
        "pre_shift":pre_shift,
        "post_logical":post_logical,
        "scalar_candidates":evaluated,
        "scalar_pass":len(hits)
    },indent=2))
if __name__=="__main__":
    main()
