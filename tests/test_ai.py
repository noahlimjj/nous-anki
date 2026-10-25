import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from nous_anki.ai_search import AISearchClient


class TestAISearch(unittest.TestCase):
    def test_missing_api_key_error(self):
        client = AISearchClient(provider="openai", api_key="")
        res = client.search_query("test question")
        self.assertFalse(res["success"])
        self.assertIn("No API key configured", res["error"])

    def test_empty_query_error(self):
        client = AISearchClient(provider="openai", api_key="sk-test12345")
        res = client.search_query("   ")
        self.assertFalse(res["success"])
        self.assertIn("Query cannot be empty", res["error"])

    def test_web_search_urls(self):
        url_google = AISearchClient.get_web_search_url("google", "myocardial infarction")
        self.assertIn("google.com/search?q=myocardial+infarction", url_google)

        url_amboss = AISearchClient.get_web_search_url("amboss", "atrial fibrillation")
        self.assertIn("next.amboss.com/us/search?q=atrial+fibrillation", url_amboss)

        url_pubmed = AISearchClient.get_web_search_url("pubmed", "statin therapy")
        self.assertIn("pubmed.ncbi.nlm.nih.gov/?term=statin+therapy", url_pubmed)


if __name__ == "__main__":
    unittest.main()
