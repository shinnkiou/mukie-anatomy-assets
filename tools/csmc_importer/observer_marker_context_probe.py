from __future__ import annotations

import argparse
import csv
import io
import json
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

MEM_TYPE = {
    0x1000000: 'MEM_IMAGE',
    0x40000: 'MEM_MAPPED',
    0x20000: 'MEM_PRIVATE',
}
PROTECT = {
    0x01: 'PAGE_NOACCESS',
    0x02: 'PAGE_READONLY',
    0x04: 'PAGE_READWRITE',
    0x08: 'PAGE_WRITECOPY',
    0x10: 'PAGE_EXECUTE',
    0x20: 'PAGE_EXECUTE_READ',
    0x40: 'PAGE_EXECUTE_READWRITE',
    0x80: 'PAGE_EXECUTE_WRITECOPY',
}


def phex(s: str) -> int:
    return int(s, 16)


def ascii_runs(b: bytes, min_len: int = 3) -> list[str]:
    pat = rb'[\x20-\x7e]{%d,}' % min_len
    return [x.decode('ascii', 'replace') for x in re.findall(pat, b)]


def utf16le_ascii_runs(b: bytes, min_len: int = 3) -> list[str]:
    out = []
    i = 0
    while i + 1 < len(b):
        start = i
        chars = []
        while i + 1 < len(b) and 0x20 <= b[i] <= 0x7e and b[i + 1] == 0:
            chars.append(chr(b[i]))
            i += 2
        if len(chars) >= min_len:
            out.append(''.join(chars))
        if i == start:
            i += 1
    return out


def inspect_capture(path: str | Path) -> dict:
    p = Path(path)
    with zipfile.ZipFile(p) as z:
        raw = z.read('marker_hits.csv').decode('utf-8-sig')
    rows = list(csv.DictReader(io.StringIO(raw)))
    groups = defaultdict(list)
    for row in rows:
        b = bytes.fromhex(row['context_hex'])
        typ = phex(row['type'])
        prot = phex(row['protect'])
        item = {
            'marker': row['marker'],
            'encoding': row['encoding'],
            'address': row['address'],
            'region_base': row['region_base'],
            'type': row['type'],
            'type_name': MEM_TYPE.get(typ, 'UNKNOWN'),
            'protect': row['protect'],
            'protect_name': PROTECT.get(prot & 0xff, 'UNKNOWN'),
            'ascii_runs': ascii_runs(b),
            'utf16le_ascii_runs': utf16le_ascii_runs(b),
        }
        groups[row['region_base']].append(item)

    region_out = []
    for base, items in sorted(groups.items(), key=lambda kv: phex(kv[0])):
        markers = Counter(i['marker'] for i in items)
        ascii_all = []
        u16_all = []
        for i in items:
            ascii_all.extend(i['ascii_runs'])
            u16_all.extend(i['utf16le_ascii_runs'])
        region_out.append({
            'region_base': base,
            'memory_type': items[0]['type_name'],
            'protection': items[0]['protect_name'],
            'markers': dict(markers),
            'addresses': [i['address'] for i in items],
            'ascii_context_fragments': ascii_all,
            'utf16le_ascii_context_fragments': u16_all,
        })

    return {
        'capture': str(p),
        'hit_count': len(rows),
        'region_count': len(region_out),
        'regions': region_out,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description='Summarize Observer marker-hit context and memory-region clustering')
    ap.add_argument('capture_zip')
    args = ap.parse_args()
    print(json.dumps(inspect_capture(args.capture_zip), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
