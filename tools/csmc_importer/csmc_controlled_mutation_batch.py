#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, shutil, sqlite3, struct, zipfile
from pathlib import Path

EXPECTED_BASE_SHA256 = "d7b36076348035a6965890ee19c00f5487de94aa6db5b23ff2459b75ae815eab"
EXPECTED_FIXTURE = "CSMC_F02_QUAD"
EXPECTED_LOGICAL = 17687
EXPECTED_STORED = 17696
PAYLOAD_OFFSET = 65
INVARIANT_START = 402 * 8
ALIGN8_LOGICAL = 17688
FRAMING_REMAINDER_START = ALIGN8_LOGICAL
XOR_MASK = 0x01

MUTATIONS = [
    *( (f"P{i:02d}", off, "PREFIX_INTERIOR") for i, off in enumerate([8,64,128,256,512,1024,1536,2048,2560,3072], 1) ),
    *( (f"B{i:02d}", INVARIANT_START + d, "INVARIANT_BOUNDARY") for i, d in enumerate([-16,-8,-1,0,1,8,16], 1) ),
    *( (f"I{i:02d}", INVARIANT_START + d, "INVARIANT_INTERIOR") for i, d in enumerate([512,4096,8192,12000], 1) ),
    ("A01", EXPECTED_LOGICAL, "ALIGNMENT_EXTENSION"),
    *( (f"R{i:02d}", FRAMING_REMAINDER_START + i - 1, "FRAMING_REMAINDER") for i in range(1,9) ),
]


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def sha256_file(p: Path) -> str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20), b''):
            h.update(chunk)
    return h.hexdigest()

def align8(n:int)->int:
    return (n+7)&~7

def read_blob(path: Path) -> tuple[int, bytes]:
    con=sqlite3.connect(str(path))
    try:
        row=con.execute("select version, character from character").fetchone()
        if row is None:
            raise ValueError("character row missing")
        version, blob=row
        if not isinstance(blob,(bytes,bytearray)):
            raise ValueError("character column is not blob")
        return int(version), bytes(blob)
    finally:
        con.close()

def parse_frame(blob: bytes) -> dict:
    off=0
    ml=struct.unpack_from('<I',blob,off)[0]; off+=4
    magic=blob[off:off+ml]; off+=ml
    kl=struct.unpack_from('<I',blob,off)[0]; off+=4
    kind=blob[off:off+kl]; off+=kl
    guid=blob[off:off+16]; off+=16
    iv,logical,stored=struct.unpack_from('<III',blob,off); off+=12
    if off != PAYLOAD_OFFSET:
        raise ValueError(f"unexpected payload offset {off}")
    if magic != b'CLIP_STUDIO_3D_DATA2' or kind != b'character' or iv != 2:
        raise ValueError("unexpected controlled envelope")
    if len(blob) != PAYLOAD_OFFSET + stored:
        raise ValueError("stored length mismatch")
    return {"logical":logical,"stored":stored,"guid_hex":guid.hex(),"inner_version":iv}

def write_blob(path: Path, version:int, blob:bytes)->None:
    con=sqlite3.connect(str(path))
    try:
        con.execute("update character set version=?, character=?", (version, sqlite3.Binary(blob)))
        con.commit()
    finally:
        con.close()

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('base_csmc', type=Path)
    ap.add_argument('out_dir', type=Path)
    ap.add_argument('--zip-out', type=Path)
    ap.add_argument('--public-manifest', type=Path)
    ns=ap.parse_args()

    if sha256_file(ns.base_csmc) != EXPECTED_BASE_SHA256:
        raise SystemExit("BASE_SHA256_MISMATCH")
    version, base_blob=read_blob(ns.base_csmc)
    frame=parse_frame(base_blob)
    if (frame['logical'],frame['stored']) != (EXPECTED_LOGICAL,EXPECTED_STORED):
        raise SystemExit("BASE_FRAME_MISMATCH")
    if align8(frame['logical']) != ALIGN8_LOGICAL:
        raise SystemExit("ALIGNMENT_RULE_MISMATCH")

    if not (0 < INVARIANT_START < ALIGN8_LOGICAL < EXPECTED_STORED+1):
        raise SystemExit("INVALID_PREREGISTERED_BOUNDARIES")
    if len({m[1] for m in MUTATIONS}) != len(MUTATIONS):
        raise SystemExit("DUPLICATE_MUTATION_OFFSET")
    if len(MUTATIONS) != 30:
        raise SystemExit("UNEXPECTED_MUTATION_COUNT")

    ns.out_dir.mkdir(parents=True, exist_ok=True)
    rows=[]
    for seq,(short_id,payload_rel,region) in enumerate(MUTATIONS,1):
        if not (0 <= payload_rel < EXPECTED_STORED):
            raise SystemExit(f"offset out of range: {payload_rel}")
        mut=bytearray(base_blob)
        blob_off=PAYLOAD_OFFSET + payload_rel
        mut[blob_off] ^= XOR_MASK
        out_name=f"CSMC_M{seq:02d}_{short_id}_{region}_{payload_rel:05d}.csmc"
        out_path=ns.out_dir/out_name
        shutil.copy2(ns.base_csmc,out_path)
        write_blob(out_path,version,bytes(mut))
        _,b2=read_blob(out_path)
        f2=parse_frame(b2)
        diffs=[i for i,(x,y) in enumerate(zip(base_blob,b2)) if x!=y]
        if len(base_blob)!=len(b2) or diffs != [blob_off]:
            raise SystemExit(f"{out_name}: blob diff is not exactly one byte: {diffs[:8]}")
        if (f2['logical'],f2['stored']) != (EXPECTED_LOGICAL,EXPECTED_STORED):
            raise SystemExit(f"{out_name}: frame changed")
        rows.append({
            "variant_id":f"M{seq:02d}",
            "filename":out_name,
            "region":region,
            "payload_relative_offset":payload_rel,
            "character_blob_offset":blob_off,
            "xor_mask_hex":"01",
            "file_sha256":sha256_file(out_path),
            "character_blob_sha256":sha256_bytes(b2),
            "character_blob_diff_byte_count":1,
            "sqlite_readback_ok":True,
            "frame_rule_still_holds":True,
            "modeler_load_result":"PENDING_MANUAL_ORACLE",
            "visual_result":"PENDING_MANUAL_ORACLE",
            "save_normalization_result":"PENDING_MANUAL_ORACLE",
        })

    manifest={
        "schema_version":"csmc_controlled_mutation_batch_v1",
        "batch_id":"CSMC_F02_SINGLE_BYTE_XOR01_30_20260914",
        "base_fixture":EXPECTED_FIXTURE,
        "base_file_sha256":EXPECTED_BASE_SHA256,
        "base_character_blob_sha256":sha256_bytes(base_blob),
        "logical_length":EXPECTED_LOGICAL,
        "stored_length":EXPECTED_STORED,
        "payload_offset":PAYLOAD_OFFSET,
        "proven_invariant_start_payload_offset":INVARIANT_START,
        "aligned_logical_length":ALIGN8_LOGICAL,
        "framing_remainder_start_payload_offset":FRAMING_REMAINDER_START,
        "mutation_rule":"exactly one character-BLOB byte XOR 0x01 per variant",
        "variant_count":len(rows),
        "raw_bytes_embedded":False,
        "semantic_promotion":False,
        "blender_emit_ready":False,
        "runtime_dispatch":False,
        "variants":rows,
    }
    mpath=ns.public_manifest or (ns.out_dir.parent/'CSMC_F02_SINGLE_BYTE_XOR01_30_PUBLIC_MANIFEST_20260914.json')
    mpath.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding='utf-8')

    if ns.zip_out:
        with zipfile.ZipFile(ns.zip_out,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for p in sorted(ns.out_dir.glob('*.csmc')):
                z.write(p,arcname=p.name)
            z.write(mpath,arcname=mpath.name)
    print(json.dumps({
        "status":"MUTATION_BATCH_READY",
        "variants":len(rows),
        "manifest":str(mpath),
        "manifest_sha256":sha256_file(mpath),
        "zip":str(ns.zip_out) if ns.zip_out else None,
        "zip_sha256":sha256_file(ns.zip_out) if ns.zip_out else None,
    },indent=2))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
