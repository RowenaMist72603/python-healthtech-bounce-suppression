import unittest

from suppression_health import InfraiClient, handle_delivery


class FakeClient(InfraiClient):
    def __init__(self):
        super().__init__("test")
        self.suppressed = []

    def send(self, to, subject, text, request_id):
        return {"message_id": "msg_test"}

    def events(self, message_id):
        return {"items": [{"type": "hard_bounce"}]}

    def suppress(self, email, request_id):
        self.suppressed.append(email)
        return {"email": email}


class SuppressionFlowTest(unittest.TestCase):
    def test_hard_bounce_is_suppressed(self):
        client = FakeClient()
        result = handle_delivery(client, "patient@example.com")
        self.assertTrue(result["hard_bounced"])
        self.assertEqual(client.suppressed, ["patient@example.com"])


if __name__ == "__main__":
    unittest.main()
