from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")
STATE = (ROOT / "assets/state-contract.md").read_text(encoding="utf-8")


class KnowledgeBaseContractTests(unittest.TestCase):
    def test_confirmed_import_takes_precedence_over_source_autodetection(self):
        self.assertRegex(SKILL, r"(?im)^- .*`import`.*fuentes confirmadas")
        self.assertRegex(SKILL, r"(?im)^- .*`interview`.*Mode B")
        self.assertIn("fuera de `docs/`", SKILL)
        self.assertIn('`"ingest"` (Mode A)', STATE)

    def test_partial_resume_uses_verified_outputs_and_writes_only_pending(self):
        self.assertRegex(SKILL, r"(?im)^.*ejecución interrumpida.*pendientes del plan confirmado")
        self.assertIn("solo los archivos pendientes", SKILL)
        self.assertIn('version >= 2', STATE)
        self.assertIn('Preserve unknown fields and other phase records', STATE)

    def test_reusing_canonical_kb_preserves_files_without_running_generation(self):
        self.assertRegex(SKILL, r"(?im)^- .*`reuse`.*10 canónicos.*sin escribir")
        self.assertRegex(SKILL, r"(?im)^.*`reuse`.*orquestador registra")
        self.assertRegex(SKILL, r"(?im)^.*KB parcial.*no sobrescrib")


if __name__ == "__main__":
    unittest.main()
