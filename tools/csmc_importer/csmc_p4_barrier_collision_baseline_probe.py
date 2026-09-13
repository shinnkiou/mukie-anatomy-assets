#!/usr/bin/env python3
"""Public-safe sub-qword collision baseline probe for CSMC P4 barriers.

Consumes already-extracted opaque payload bytes and reports only aggregate counts and
statistical summaries. It never prints source unit values.
"""
from __future__ import annotations
import argparse, json, math, zlib
from collections import Counter
from pathlib import Path


def units(data: bytes, unit: int, offset: int = 0):
    end = len(data) - ((len(data) - offset) % unit)
    return [data[i:i+unit] for i in range(offset, end, unit)]


def entropy(data: bytes) -> float:
    if not data: return 0.0
    c = Counter(data); n = len(data)
    return -sum((v/n) * math.log2(v/n) for v in c.values())


def histogram(data: bytes):
    c = Counter(data); n = len(data)
    return [c.get(i, 0)/n if n else 0.0 for i in range(256)]


def js_divergence(a: bytes, b: bytes) -> float:
    p, q = histogram(a), histogram(b)
    out = 0.0
    for x, y in zip(p, q):
        m = (x+y)/2
        if x: out += 0.5*x*math.log2(x/m)
        if y: out += 0.5*y*math.log2(y/m)
    return out


def expected_distinct_hits(query_distinct: int, target_units: int, bits: int) -> float:
    space = 2 ** bits
    p = 1.0 - (1.0 - 1.0/space) ** target_units
    return query_distinct * p


def analyze(clip: bytes, csmc: bytes, *, clip_start_block: int, clip_end_block: int,
            csmc_start_block: int, csmc_end_block: int, unit: int = 4) -> dict:
    if unit <= 0: raise ValueError('unit must be positive')
    A = clip[clip_start_block*8:clip_end_block*8]
    B = csmc[csmc_start_block*8:csmc_end_block*8]
    qa = set(units(A, unit)); qb = set(units(B, unit))
    local = len(qa & qb)
    found_a=set(); found_b=set()
    for v in units(csmc, unit):
        if v in qa:
            found_a.add(v)
            if len(found_a)==len(qa): break
    for v in units(clip, unit):
        if v in qb:
            found_b.add(v)
            if len(found_b)==len(qb): break
    a_in_b=len(found_a); b_in_a=len(found_b)
    exp_a = expected_distinct_hits(len(qa), len(csmc)//unit, unit*8)
    exp_b = expected_distinct_hits(len(qb), len(clip)//unit, unit*8)
    return {
      'schema_version':'csmc_p4_barrier_collision_baseline_v1',
      'unit_bytes':unit,
      'clip_barrier_bytes':len(A), 'csmc_barrier_bytes':len(B),
      'clip_distinct_units':len(qa), 'csmc_distinct_units':len(qb),
      'local_cross_barrier_shared_distinct_units':local,
      'clip_barrier_units_found_anywhere_in_csmc':a_in_b,
      'csmc_barrier_units_found_anywhere_in_clip':b_in_a,
      'uniform_random_expected_clip_to_csmc_hits':exp_a,
      'uniform_random_expected_csmc_to_clip_hits':exp_b,
      'clip_to_csmc_observed_expected_ratio':(a_in_b/exp_a if exp_a else None),
      'csmc_to_clip_observed_expected_ratio':(b_in_a/exp_b if exp_b else None),
      'clip_barrier_entropy_bits_per_byte':entropy(A),
      'csmc_barrier_entropy_bits_per_byte':entropy(B),
      'clip_zlib_ratio':(len(zlib.compress(A,9))/len(A) if A else None),
      'csmc_zlib_ratio':(len(zlib.compress(B,9))/len(B) if B else None),
      'byte_histogram_js_divergence_bits':js_divergence(A,B),
      'interpretation_guard':'Observed sub-qword overlap near the uniform-random baseline is not evidence of encryption/compression; it only weakens literal/subword reuse as an owner mapping strategy.'
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--clip-payload',type=Path,required=True); ap.add_argument('--csmc-payload',type=Path,required=True)
    ap.add_argument('--clip-start-block',type=int,required=True); ap.add_argument('--clip-end-block',type=int,required=True); ap.add_argument('--csmc-start-block',type=int,required=True); ap.add_argument('--csmc-end-block',type=int,required=True); ap.add_argument('--unit',type=int,default=4); ap.add_argument('--json-out',type=Path)
    ns=ap.parse_args(); r=analyze(ns.clip_payload.read_bytes(),ns.csmc_payload.read_bytes(),clip_start_block=ns.clip_start_block,clip_end_block=ns.clip_end_block,csmc_start_block=ns.csmc_start_block,csmc_end_block=ns.csmc_end_block,unit=ns.unit); t=json.dumps(r,indent=2,sort_keys=True); print(t); ns.json_out and ns.json_out.write_text(t+'\n',encoding='utf-8')
if __name__=='__main__': main()
