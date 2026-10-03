import unittest
from ai_classifier import classify_text


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


if __name__ == "__main__":
    unittest.main()
