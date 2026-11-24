import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/proofpecker/scripts"))
import proofpecker as p
import pecker_models as m


class ReviewTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.args = argparse.Namespace(example=True, plan=None, roles="implementation,evidence", files=[], claim=None,
                                       language="English", follow_up=None, out=self.root / "run")
        with contextlib.redirect_stdout(io.StringIO()):
            self.run_dir = p.prepare(self.args)
        self.body = p.read_packet(self.run_dir)
        self.report = {"summary": "Reviewed the marker.", "missing": [], "findings": []}

    def record(self, role, report=None, session=None):
        p.store_receipt(self.run_dir, self.body, role, json.dumps(report or self.report), session or role, {})

    def finding(self):
        return {"severity":"medium", "claim_id":"stop", "path":"capture.txt", "trigger":"marker already present",
                "impact":"a redundant write is invisible", "evidence":"same final set"}

    def test_distinct_bindings_and_scope(self):
        self.assertNotEqual(p.reading_hash(self.body,"implementation"), p.reading_hash(self.body,"evidence"))
        narrower = dict(self.body, roles=["implementation"])
        self.assertNotEqual(p.reading_hash(narrower,"implementation"), p.reading_hash(self.body,"implementation"))
        for role in self.body["roles"]:
            self.assertIn("capture.txt", p.messages(self.body, role)[1])
        self.assertEqual(p.assess(self.run_dir)["missing_roles"], self.body["roles"])

    def test_receipts_and_reused_sessions(self):
        self.record("evidence", dict(self.report, findings=[self.finding()]), "same")
        with self.assertRaises(FileExistsError):
            self.record("evidence")
        self.record("implementation", session="same")
        with self.assertRaisesRegex(ValueError, "reused"):
            p.assess(self.run_dir)

    def test_missing_material_and_scope(self):
        self.record("evidence", dict(self.report, missing=["First observed run"]))
        self.record("implementation")
        state = p.assess(self.run_dir)
        self.assertEqual(state["review_execution"], "complete")
        self.assertTrue(state["missing_material"])
        self.assertFalse(state["release_authorized"])
        with self.assertRaises(ValueError):
            p.valid(self.body, dict(self.report, findings=[dict(self.finding(), path="unseen.log")]))

    def test_original_survives_targeted_followup(self):
        self.record("evidence", dict(self.report, findings=[self.finding()]))
        previous = (self.run_dir/"evidence.receipt.json").read_bytes()
        self.args.roles = "evidence"
        self.args.follow_up = str(self.run_dir) + "#evidence.1"
        self.args.out = self.root/"follow"
        with contextlib.redirect_stdout(io.StringIO()):
            new = p.prepare(self.args)
        body = p.read_packet(new)
        self.assertIn("prior_receipt", body["follow_up"])
        report = dict(self.report, disposition={"status":"open","path":"capture.txt","evidence":"still ambiguous"})
        with self.assertRaisesRegex(ValueError,"fresh"):
            p.store_receipt(new, body, "evidence", json.dumps(report), "evidence", {})
        p.store_receipt(new, body, "evidence", json.dumps(report), "different", {})
        self.assertEqual(p.assess(new)["finding_resolution"], "open")
        self.assertEqual(previous, (self.run_dir/"evidence.receipt.json").read_bytes())

    def test_failed_provider_is_not_clean_and_resume_skips_completed(self):
        self.record("implementation")
        with patch.object(p, "invoke", return_value=("bad json", {"provider":"test"})) as model:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(p.run_reviews(self.run_dir, {"implementation":"test/m","evidence":"test/m"}), 2)
            self.assertEqual(model.call_count, 1)
        self.assertEqual(p.assess(self.run_dir)["missing_roles"], ["evidence"])

    def test_mixed_provider_reports_are_bound_to_separate_requests(self):
        def result(model, system, prompt):
            provider, name = m.engine(model)
            self.assertIn("capture.txt", prompt)
            return json.dumps(self.report), {"provider": provider, "requested_model": name,
                                              "returned_model": name, "response_id": "fixture"}
        choices = {"implementation": "anthropic/test-a", "evidence": "gemini/test-b"}
        with patch.object(p, "invoke", side_effect=result), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(p.run_reviews(self.run_dir, choices), 0)
        reviewers = p.assess(self.run_dir)["reviewers"]
        self.assertEqual(reviewers["implementation"]["model"], "test-a")
        self.assertEqual(reviewers["evidence"]["model"], "test-b")
        self.assertNotEqual(reviewers["implementation"]["session"], reviewers["evidence"]["session"])

    def test_preserve_text_and_detect_drift(self):
        (self.root/"crlf.txt").write_bytes(b"a\r\nb\n")
        self.args.example = False
        self.args.plan = self.root/"plan.json"
        self.args.plan.write_text(json.dumps({"claims":[{"id":"a","claim":"line endings","files":["crlf.txt"]}]}))
        self.assertEqual(p.packet(self.args)["files"]["crlf.txt"]["text"], "a\r\nb\n")
        archive = p.load_json(self.run_dir/"packet.json")
        archive["packet"]["files"]["capture.txt"]["text"] += "changed"
        (self.run_dir/"packet.json").write_text(json.dumps(archive))
        with self.assertRaises(ValueError):
            p.read_packet(self.run_dir)


class ModelsTest(unittest.TestCase):
    def test_native_and_chat_presets(self):
        env = {key:"fixture-token" for _,key in m.ENGINES.values() if key}
        env["PROOFPECKER_COMPATIBLE_URL"] = "http://localhost:9999/v1"
        with patch.dict(os.environ, env, clear=True):
            for provider in m.ENGINES:
                with self.subTest(provider=provider):
                    req = m.api_request(provider+"/unit-model","role","packet")
                    self.assertNotIn("fixture-token",req.full_url)
                    self.assertIn("packet",req.data.decode())
                    body = json.loads(req.data)
                    if provider == "openai":
                        self.assertFalse(body["store"])
                        self.assertTrue(req.full_url.endswith("/responses"))
                    elif provider == "anthropic":
                        self.assertIn("Anthropic-version",req.headers)
                    elif provider == "gemini":
                        self.assertIn("X-goog-api-key",req.headers)
                    else:
                        self.assertTrue(req.full_url.endswith("/chat/completions"))
                    self.assertNotIn("tools",body)

    def test_parse_provider_responses_and_reject_truncation(self):
        responses = {"openai":{"status":"completed","output":[{"type":"message","content":[{"type":"output_text","text":"ok"}]}]},
                     "anthropic":{"stop_reason":"end_turn","content":[{"type":"text","text":"ok"}]},
                     "gemini":{"candidates":[{"finishReason":"STOP","content":{"parts":[{"text":"ok"}]}}]}}
        for provider in m.ENGINES:
            payload = responses.get(provider,{"choices":[{"finish_reason":"stop","message":{"content":"ok"}}]})
            self.assertEqual(m.response_text(provider,payload),"ok")
        with self.assertRaises(ValueError):
            m.response_text("compatible",{"choices":[{"finish_reason":"length"}]})

    def test_mixed_role_configuration(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY":"a", "ANTHROPIC_API_KEY":"b"}, clear=True):
            args = argparse.Namespace(model="openai/model-a", engine=["implementation=anthropic/model-b","evidence=ollama/local"])
            result = p.model_choices(args,["design","implementation","evidence"])
            self.assertEqual(result,{"design":"openai/model-a","implementation":"anthropic/model-b","evidence":"ollama/local"})

if __name__ == "__main__":
    unittest.main()
