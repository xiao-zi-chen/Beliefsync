import json
import os
import unittest

from beliefsync.llm import LLMConfig, _normalize_unit_score, _parse_json_payload


class LLMTests(unittest.TestCase):
    def test_parse_json_payload_from_fenced_block(self):
        payload = _parse_json_payload("```json\n[{\"belief_type\": \"bug_localization\", \"claim\": \"x\"}]\n```")
        self.assertEqual(payload[0]["belief_type"], "bug_localization")

    def test_llm_config_from_env_prefers_generic_vars(self):
        old_values = {k: os.environ.get(k) for k in ["BELIEFSYNC_LLM_API_KEY", "BELIEFSYNC_LLM_BASE_URL", "BELIEFSYNC_LLM_MODEL", "KIMI_API_KEY"]}
        try:
            os.environ["BELIEFSYNC_LLM_API_KEY"] = "generic-key"
            os.environ["BELIEFSYNC_LLM_BASE_URL"] = "https://example.com/v1"
            os.environ["BELIEFSYNC_LLM_MODEL"] = "test-model"
            os.environ["KIMI_API_KEY"] = "kimi-key"
            config = LLMConfig.from_env()
            self.assertEqual(config.api_key, "generic-key")
            self.assertEqual(config.base_url, "https://example.com/v1")
            self.assertEqual(config.model, "test-model")
        finally:
            for key, value in old_values.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_normalize_unit_score_handles_ten_scale(self):
        self.assertEqual(_normalize_unit_score(8), 0.8)
        self.assertEqual(_normalize_unit_score(120), 1.0)


if __name__ == "__main__":
    unittest.main()
