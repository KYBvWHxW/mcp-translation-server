from locust import HttpUser, task, between
import json

class TranslationUser(HttpUser):
    wait_time = between(1, 2)
    
    def on_start(self):
        """Setup authentication if needed."""
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer ${MCP_API_TOKEN}"
        }
        
        # Common test cases
        self.test_cases = [
            {"text": "ere amba de tehe", "context": "location"},
            {"text": "amba moo i baru", "context": "direction"},
            {"text": "tere niyalma", "context": "person"},
            {"text": "ere bithe be", "context": "object"},
        ]
    
    @task(3)
    def translate_simple(self):
        """Test simple translation."""
        test_case = self.test_cases[0]
        self.client.post(
            "/api/v1/translate",
            json={"text": test_case["text"], "context": test_case["context"]},
            headers=self.headers
        )
    
    @task(2)
    def translate_with_context(self):
        """Test translation with different contexts."""
        for test_case in self.test_cases[1:]:
            self.client.post(
                "/api/v1/translate",
                json={"text": test_case["text"], "context": test_case["context"]},
                headers=self.headers
            )
    
    @task(1)
    def batch_translate(self):
        """Test batch translation."""
        texts = [case["text"] for case in self.test_cases]
        self.client.post(
            "/api/v1/batch_translate",
            json={"texts": texts},
            headers=self.headers
        )
    
    @task(1)
    def dictionary_lookup(self):
        """Test dictionary lookups."""
        words = ["amba", "niyalma", "bithe"]
        for word in words:
            self.client.get(
                f"/api/v1/dictionary/{word}",
                headers=self.headers
            )
