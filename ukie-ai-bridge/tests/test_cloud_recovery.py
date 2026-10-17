import copy
import unittest

from bridge import cloud_recovery


BASE = "UKIE_PHYSICAL_ACCEPTANCE__BRIDGE_PTEST__PHYSICAL_ACCEPTANCE_TEST.zip"


def complete_discovery(ids=None, sizes=None):
    ids = ids or {"zip": "z1", "sha256": "s1", "handoff": "h1"}
    sizes = sizes or {"zip": 1000, "sha256": 80, "handoff": 500}
    triplet = {
        "zip": {"file_id": ids["zip"], "name": BASE, "size": sizes["zip"]},
        "sha256": {"file_id": ids["sha256"], "name": BASE + ".sha256", "size": sizes["sha256"]},
        "handoff": {"file_id": ids["handoff"], "name": BASE + ".handoff.json", "size": sizes["handoff"]},
    }
    return {
        "schema_version": "ukie_cloud_discovery_v1",
        "status": "DISCOVERED",
        "complete": [{"base_name": BASE, "status": "COMPLETE", "triplet": triplet}],
        "incomplete": [],
        "ambiguous": [],
    }


def incomplete_discovery():
    return {
        "schema_version": "ukie_cloud_discovery_v1",
        "status": "DISCOVERED",
        "complete": [],
        "incomplete": [{"base_name": BASE, "status": "INCOMPLETE", "missing": ["sha256"]}],
        "ambiguous": [],
    }


def ambiguous_discovery():
    return {
        "schema_version": "ukie_cloud_discovery_v1",
        "status": "DISCOVERED",
        "complete": [],
        "incomplete": [],
        "ambiguous": [{"base_name": BASE, "status": "AMBIGUOUS", "counts": {"zip": 2, "sha256": 1, "handoff": 1}}],
    }


def absent_discovery():
    return {
        "schema_version": "ukie_cloud_discovery_v1",
        "status": "WAITING_FOR_SYNC",
        "complete": [],
        "incomplete": [],
        "ambiguous": [],
    }


def verified_intake(sha="a" * 64, ids=None):
    ids = ids or {"zip": "z1", "sha256": "s1", "handoff": "h1"}
    return {
        "schema_version": "ukie_cloud_intake_v1",
        "status": "DRIVE_READBACK_VERIFIED",
        "acceptance_id": "PHYSICAL_ACCEPTANCE_TEST",
        "release_key": "BRIDGE_PTEST",
        "bridge_version": "0.TEST",
        "commit_sha": "b" * 40,
        "workflow_run_id": 123,
        "file_name": BASE,
        "byte_size": 1000,
        "sha256": sha,
        "triplet_verified": True,
        "acceptance_evidence_status": "ACCEPTANCE_EVIDENCE_VALID",
        "local_core_ready": True,
        "local_gpu_render_ready": False,
        "cloud_presence_proven": True,
        "drive_readback_proven": True,
        "provider": {"provider": "GOOGLE_DRIVE", "file_ids": ids},
        "physical_provenance": True,
        "ready_for_ai": False,
        "promotion_performed": False,
    }


class CloudRecoveryTests(unittest.TestCase):
    def test_absent_initial_state_waits_without_failure(self):
        state = cloud_recovery.reconcile_candidate(BASE, absent_discovery())
        self.assertEqual(state["status"], "WAITING_FOR_SYNC")
        self.assertFalse(state["ready_for_ai"])
        self.assertFalse(state["promotion_performed"])

    def test_incomplete_then_complete_progresses_without_failure(self):
        first = cloud_recovery.reconcile_candidate(BASE, incomplete_discovery())
        self.assertEqual(first["status"], "INCOMPLETE")
        second = cloud_recovery.reconcile_candidate(BASE, complete_discovery(), first)
        self.assertEqual(second["status"], "COMPLETE")
        self.assertEqual(second["next_action"], "FETCH_THREE_FILES_AND_VERIFY_READBACK")

    def test_repeated_same_complete_scan_is_idempotent(self):
        first = cloud_recovery.reconcile_candidate(BASE, complete_discovery())
        second = cloud_recovery.reconcile_candidate(BASE, complete_discovery(), first)
        self.assertTrue(second["idempotent_replay"])
        self.assertEqual(second["revision"], first["revision"])

    def test_complete_with_physical_provider_intake_becomes_drive_verified(self):
        state = cloud_recovery.reconcile_candidate(BASE, complete_discovery(), intake=verified_intake())
        self.assertEqual(state["status"], "DRIVE_VERIFIED")
        self.assertTrue(state["physical_provenance"])
        self.assertEqual(state["verified_sha256"], "a" * 64)
        self.assertFalse(state["ready_for_ai"])
        self.assertFalse(state["promotion_performed"])

    def test_verified_same_triplet_without_refetch_never_downgrades(self):
        verified = cloud_recovery.reconcile_candidate(BASE, complete_discovery(), intake=verified_intake())
        observed = cloud_recovery.reconcile_candidate(BASE, complete_discovery(), verified)
        self.assertEqual(observed["status"], "DRIVE_VERIFIED")
        self.assertEqual(observed["verified_sha256"], verified["verified_sha256"])
        replay = cloud_recovery.reconcile_candidate(BASE, complete_discovery(), observed)
        self.assertTrue(replay["idempotent_replay"])
        self.assertEqual(replay["status"], "DRIVE_VERIFIED")

    def test_verified_temporarily_missing_does_not_erase_proof(self):
        verified = cloud_recovery.reconcile_candidate(BASE, complete_discovery(), intake=verified_intake())
        missing = cloud_recovery.reconcile_candidate(BASE, absent_discovery(), verified)
        self.assertEqual(missing["status"], "DRIVE_VERIFIED")
        self.assertEqual(missing["verified_sha256"], verified["verified_sha256"])

    def test_verified_temporarily_incomplete_does_not_erase_proof(self):
        verified = cloud_recovery.reconcile_candidate(BASE, complete_discovery(), intake=verified_intake())
        partial = cloud_recovery.reconcile_candidate(BASE, incomplete_discovery(), verified)
        self.assertEqual(partial["status"], "DRIVE_VERIFIED")

    def test_changed_file_ids_after_verification_are_sticky_block(self):
        verified = cloud_recovery.reconcile_candidate(BASE, complete_discovery(), intake=verified_intake())
        changed = complete_discovery({"zip": "z2", "sha256": "s1", "handoff": "h1"})
        blocked = cloud_recovery.reconcile_candidate(BASE, changed, verified)
        self.assertEqual(blocked["status"], "BLOCKED")
        self.assertEqual(blocked["blocked_reason"], "VERIFIED_EVIDENCE_FILE_IDS_CHANGED")
        restored_scan = cloud_recovery.reconcile_candidate(BASE, complete_discovery(), blocked)
        self.assertEqual(restored_scan["status"], "BLOCKED")
        self.assertEqual(restored_scan["blocked_reason"], "VERIFIED_EVIDENCE_FILE_IDS_CHANGED")

    def test_size_metadata_change_same_ids_is_not_misclassified_as_id_change(self):
        verified = cloud_recovery.reconcile_candidate(BASE, complete_discovery(), intake=verified_intake())
        sizes = {"zip": 2000, "sha256": 81, "handoff": 600}
        observed = cloud_recovery.reconcile_candidate(BASE, complete_discovery(sizes=sizes), verified)
        self.assertEqual(observed["status"], "DRIVE_VERIFIED")
        self.assertIsNone(observed["blocked_reason"])

    def test_changed_sha_same_file_ids_after_verification_blocks(self):
        verified = cloud_recovery.reconcile_candidate(BASE, complete_discovery(), intake=verified_intake("a" * 64))
        blocked = cloud_recovery.reconcile_candidate(BASE, complete_discovery(), verified, verified_intake("c" * 64))
        self.assertEqual(blocked["status"], "BLOCKED")
        self.assertEqual(blocked["blocked_reason"], "VERIFIED_EVIDENCE_SHA_CHANGED")

    def test_provider_ids_must_match_discovery(self):
        with self.assertRaises(cloud_recovery.CloudRecoveryError):
            cloud_recovery.reconcile_candidate(
                BASE,
                complete_discovery(),
                intake=verified_intake(ids={"zip": "wrong", "sha256": "s1", "handoff": "h1"}),
            )

    def test_nonphysical_intake_cannot_become_verified(self):
        intake = verified_intake()
        intake["physical_provenance"] = False
        with self.assertRaises(cloud_recovery.CloudRecoveryError):
            cloud_recovery.reconcile_candidate(BASE, complete_discovery(), intake=intake)

    def test_ambiguous_blocks_but_does_not_promote(self):
        state = cloud_recovery.reconcile_candidate(BASE, ambiguous_discovery())
        self.assertEqual(state["status"], "BLOCKED")
        self.assertEqual(state["blocked_reason"], "AMBIGUOUS_DUPLICATE_FILES")
        self.assertFalse(state["ready_for_ai"])
        self.assertFalse(state["promotion_performed"])

    def test_previous_identity_mismatch_is_rejected(self):
        previous = cloud_recovery.reconcile_candidate(BASE, complete_discovery())
        previous = copy.deepcopy(previous)
        previous["base_name"] = "UKIE_PHYSICAL_ACCEPTANCE__BRIDGE_OTHER__PHYSICAL_ACCEPTANCE_OTHER.zip"
        with self.assertRaises(cloud_recovery.CloudRecoveryError):
            cloud_recovery.reconcile_candidate(BASE, complete_discovery(), previous)


if __name__ == "__main__":
    unittest.main()
