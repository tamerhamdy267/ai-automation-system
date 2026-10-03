import unittest
from ai_classifier import classify_text, should_escalate


class TestClassifier(unittest.TestCase):

    def test_refund_is_support(self):
        self.assertEqual(
            classify_text("I want a refund for my purchase from 10 days ago."),
            "Support"
        )

    def test_old_refund_is_support(self):
        self.assertEqual(
            classify_text("I want a refund for my purchase from 45 days ago."),
            "Support"
        )

    def test_order_is_support(self):
        self.assertEqual(
            classify_text("Where is my order?"),
            "Support"
        )

    def test_api_issue_is_technical(self):
        self.assertEqual(
            classify_text("The API is returning an error."),
            "Technical"
        )

    def test_pricing_is_sales(self):
        self.assertEqual(
            classify_text("How much does your enterprise plan cost?"),
            "Sales"
        )


class TestEscalation(unittest.TestCase):

    def test_recent_refund_no_escalation(self):
        self.assertFalse(
            should_escalate(
                "Support",
                "I want a refund for my purchase from 10 days ago."
            )
        )

    def test_old_refund_escalation(self):
        self.assertTrue(
            should_escalate(
                "Support",
                "I want a refund for my purchase from 45 days ago."
            )
        )

    def test_complaint_escalation(self):
        self.assertTrue(
            should_escalate(
                "Support",
                "I want to make a complaint."
            )
        )

    def test_legal_escalation(self):
        self.assertTrue(
            should_escalate(
                "Support",
                "I need help with a legal issue."
            )
        )

    def test_manager_escalation(self):
        self.assertTrue(
            should_escalate(
                "Support",
                "Please let me speak to a manager."
            )
        )

    def test_urgent_escalation(self):
        self.assertTrue(
            should_escalate(
                "Support",
                "This is urgent and I need help."
            )
        )

    def test_security_escalation(self):
        self.assertTrue(
            should_escalate(
                "Technical",
                "There may have been unauthorized access."
            )
        )

    def test_normal_technical_no_escalation(self):
        self.assertFalse(
            should_escalate(
                "Technical",
                "The API is returning an error."
            )
        )

    def test_normal_support_no_escalation(self):
        self.assertFalse(
            should_escalate(
                "Support",
                "Where is my order?"
            )
        )


if __name__ == "__main__":
    unittest.main()