import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]


def load_script(module_name: str, relative_path: str):
    spec = importlib.util.spec_from_file_location(module_name, ROOT_DIR / relative_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


readiness_gate = load_script("readiness_gate", "scripts/readiness-gate.py")
record_evidence = load_script("record_readiness_evidence", "scripts/record-readiness-evidence.py")


class ReadinessEvidenceTest(unittest.TestCase):
    def test_gate_contracts_match_between_validator_recorder_and_template(self):
        template = json.loads((ROOT_DIR / "docs" / "readiness-evidence.example.json").read_text())

        self.assertEqual(record_evidence.RUNTIME_GATES, readiness_gate.RUNTIME_GATES)
        self.assertEqual(record_evidence.EXPECTED_GATE_COMMAND_FRAGMENTS, readiness_gate.EXPECTED_GATE_COMMAND_FRAGMENTS)
        self.assertEqual(template["schema_version"], readiness_gate.EVIDENCE_SCHEMA_VERSION)
        self.assertEqual(sorted(template["gates"]), sorted(readiness_gate.RUNTIME_GATES))

        for gate, fragments in readiness_gate.EXPECTED_GATE_COMMAND_FRAGMENTS.items():
            command = template["gates"][gate]["command"]
            for fragment in fragments:
                self.assertIn(fragment, command)

    def test_missing_evidence_is_not_invalid(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = readiness_gate.validate_runtime_evidence(Path(tmpdir) / "missing.json")

        self.assertEqual(result["status"], "missing")
        self.assertEqual(result["verified_gates"], [])
        self.assertEqual(result["failures"], [])

    def test_valid_verified_gate_requires_matching_command(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence = Path(tmpdir) / "readiness-evidence.json"
            evidence.write_text(
                json.dumps(
                    {
                        "schema_version": readiness_gate.EVIDENCE_SCHEMA_VERSION,
                        "generated_at": "2026-08-22T00:00:00+07:00",
                        "environment": "unit-test",
                        "gates": {
                            "llm_live_structured_output": {
                                "verified": True,
                                "verified_at": "2026-08-22T00:00:00+07:00",
                                "command": "PYTHONPATH=services/llm-parser python3 -m llm_parser.cli structured-smoke",
                                "evidence": "ok=true intent=CREATE_INVOICE item_count=2",
                            }
                        },
                    }
                )
            )

            result = readiness_gate.validate_runtime_evidence(evidence)

        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["verified_gates"], ["llm_live_structured_output"])

    def test_wrong_command_makes_evidence_invalid_and_unverified(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence = Path(tmpdir) / "readiness-evidence.json"
            evidence.write_text(
                json.dumps(
                    {
                        "schema_version": readiness_gate.EVIDENCE_SCHEMA_VERSION,
                        "generated_at": "2026-08-22T00:00:00+07:00",
                        "environment": "unit-test",
                        "gates": {
                            "llm_live_structured_output": {
                                "verified": True,
                                "verified_at": "2026-08-22T00:00:00+07:00",
                                "command": "./scripts/test-telegram.sh",
                                "evidence": "ok=true",
                            }
                        },
                    }
                )
            )

            result = readiness_gate.validate_runtime_evidence(evidence)

        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["verified_gates"], [])
        self.assertIn("llm_live_structured_output: command must include 'llm_parser.cli structured-smoke'", result["failures"])

    def test_secret_like_evidence_is_invalid(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence = Path(tmpdir) / "readiness-evidence.json"
            evidence.write_text(
                json.dumps(
                    {
                        "schema_version": readiness_gate.EVIDENCE_SCHEMA_VERSION,
                        "generated_at": "2026-08-22T00:00:00+07:00",
                        "environment": "unit-test",
                        "gates": {},
                        "note": "token=super-secret-value",
                    }
                )
            )

            result = readiness_gate.validate_runtime_evidence(evidence)

        self.assertEqual(result["status"], "invalid")
        self.assertIn("evidence file appears to contain a secret-like value", result["failures"])

    def test_mysql_pwd_evidence_is_invalid(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence = Path(tmpdir) / "readiness-evidence.json"
            evidence.write_text(
                json.dumps(
                    {
                        "schema_version": readiness_gate.EVIDENCE_SCHEMA_VERSION,
                        "generated_at": "2026-08-22T00:00:00+07:00",
                        "environment": "unit-test",
                        "gates": {},
                        "note": "MYSQL_PWD=should-not-be-here",
                    }
                )
            )

            result = readiness_gate.validate_runtime_evidence(evidence)

        self.assertEqual(result["status"], "invalid")
        self.assertIn("evidence file appears to contain a secret-like value", result["failures"])

    def test_recorder_rejects_command_that_does_not_match_gate(self):
        with self.assertRaises(SystemExit):
            record_evidence.validate_gate_command("llm_live_structured_output", "./scripts/test-telegram.sh")

    def test_recorder_rejects_secret_like_command(self):
        with self.assertRaises(SystemExit):
            record_evidence.assert_no_secret_like_value(
                "MYSQL_PWD=should-not-be-here ./scripts/validate-db.sh",
                "command",
            )

    def test_recorder_rejects_secret_like_environment(self):
        with self.assertRaises(SystemExit):
            record_evidence.assert_no_secret_like_value(
                "staging token=should-not-be-here",
                "environment",
            )

    def test_recorder_rejects_existing_evidence_file_with_secret_like_value(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence = Path(tmpdir) / "readiness-evidence.json"
            evidence.write_text(
                json.dumps(
                    {
                        "schema_version": record_evidence.EVIDENCE_SCHEMA_VERSION,
                        "generated_at": "2026-08-22T00:00:00+07:00",
                        "environment": "unit-test",
                        "gates": {},
                        "note": "api_key=should-not-be-here",
                    }
                )
            )

            with self.assertRaises(SystemExit):
                record_evidence.load_or_initialize_payload(evidence, Path(tmpdir) / "missing-template.json", "unit-test")

    def test_recorder_allows_matching_command(self):
        record_evidence.validate_gate_command(
            "llm_live_structured_output",
            "PYTHONPATH=services/llm-parser python3 -m llm_parser.cli structured-smoke",
        )


if __name__ == "__main__":
    unittest.main()
