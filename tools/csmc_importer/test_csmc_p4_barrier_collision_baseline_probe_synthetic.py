from csmc_p4_barrier_collision_baseline_probe import analyze

clip = bytearray(bytes((i*17+3)%256 for i in range(8*80)))
csmc = bytearray(bytes((i*29+11)%256 for i in range(8*90)))
clip[10*8:10*8+4] = b'ABCD'
csmc[12*8:12*8+4] = b'ABCD'
r=analyze(bytes(clip),bytes(csmc),clip_start_block=10,clip_end_block=20,csmc_start_block=12,csmc_end_block=22,unit=4)
assert r['schema_version']=='csmc_p4_barrier_collision_baseline_v1'
assert r['local_cross_barrier_shared_distinct_units'] >= 1
assert r['clip_barrier_units_found_anywhere_in_csmc'] >= 1
assert r['csmc_barrier_units_found_anywhere_in_clip'] >= 1
assert r['uniform_random_expected_clip_to_csmc_hits'] > 0
assert 0 <= r['byte_histogram_js_divergence_bits'] <= 1
print('synthetic barrier collision baseline PASS')
