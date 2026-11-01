import unittest
from bigbungi.model_access import availability

class ModelAccessTests(unittest.TestCase):
    def test_official_table_free_and_paid_columns_are_distinguished(self):
        html='''<h2 id="gemini-test">Example</h2><table><tr><th>Price</th><th>Free Tier</th><th>Paid Tier</th></tr><tr><td>Input price</td><td>Free of charge</td><td>$0.10</td></tr><tr><td>Output price</td><td>Free of charge</td><td>$0.40</td></tr></table>'''
        self.assertTrue(availability(html,['gemini-test'])['gemini-test']['available'])
        self.assertFalse(availability(html.replace('Free of charge','Not available'),['gemini-test'])['gemini-test']['available'])
        self.assertIsNone(availability(html,['gemini-new'])['gemini-new']['available'])

    def test_missing_or_changed_markup_is_unknown_not_free(self):
        self.assertIsNone(availability('<h2 id="gemini-test">Free Tier</h2>', ['gemini-test'])['gemini-test']['available'])
