from datetime import datetime, timedelta, timezone
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bridge.auth_health import evaluate_auth_health, next_health_check


class AuthHealthTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 10, 12, 0, 0, tzinfo=timezone.utc)

    def test_connected_without_provider_expiry_is_not_claimed_ready(self):
        result = evaluate_auth_health(
            provider="google",
            session_connected=True,
            token_expires_at=None,
            refresh_available=False,
            now=self.now,
        )
        self.assertEqual(result.status, "CONNECTED")
        self.assertIsNone(result.seconds_remaining)

    def test_healthy_token_is_ready(self):
        expires = (self.now + timedelta(hours=2)).isoformat()
        result = evaluate_auth_health(
            provider="google",
            session_connected=True,
            token_expires_at=expires,
            refresh_available=True,
            now=self.now,
        )
        self.assertEqual(result.status, "TOKEN_READY")
        self.assertFalse(result.refresh_attempt_due)

    def test_expiring_token_requests_refresh(self):
        expires = (self.now + timedelta(minutes=10)).isoformat()
        result = evaluate_auth_health(
            provider="google",
            session_connected=True,
            token_expires_at=expires,
            refresh_available=True,
            now=self.now,
        )
        self.assertEqual(result.status, "TOKEN_EXPIRING")
        self.assertTrue(result.refresh_attempt_due)
        self.assertFalse(result.reauth_due)

    def test_near_expiry_without_refresh_requires_reauth(self):
        expires = (self.now + timedelta(minutes=4)).isoformat()
        result = evaluate_auth_health(
            provider="google",
            session_connected=True,
            token_expires_at=expires,
            refresh_available=False,
            now=self.now,
        )
        self.assertEqual(result.status, "REAUTH_REQUIRED")
        self.assertTrue(result.reauth_due)

    def test_refresh_failure_requires_reauth(self):
        result = evaluate_auth_health(
            provider="google",
            session_connected=True,
            token_expires_at=(self.now + timedelta(hours=1)).isoformat(),
            refresh_available=True,
            refresh_failed=True,
            now=self.now,
        )
        self.assertEqual(result.status, "REAUTH_REQUIRED")

    def test_health_check_frequency_increases_near_expiry(self):
        expires = (self.now + timedelta(minutes=20)).isoformat()
        nxt = datetime.fromisoformat(next_health_check(token_expires_at=expires, now=self.now))
        self.assertEqual(int((nxt - self.now).total_seconds()), 60)


if __name__ == "__main__":
    unittest.main()
