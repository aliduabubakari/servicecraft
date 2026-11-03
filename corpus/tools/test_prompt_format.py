"""Prompt publication invariants, using fixtures with no reference graph or oracle."""

import json
import tempfile
import unittest
from pathlib import Path

from prompt_format import HEADINGS, render_prompt
from sync_prompts import sync_prompts


class PromptPublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.case = self.root / "pipelines" / "001_example"
        (self.case / "inputs").mkdir(parents=True)
        (self.case / "inputs" / "data.csv").write_text("id,value,unused\n1,2,3\n")
        (self.case / "description.md").write_text(
            "# Example\n\nBuild independent branches that converge.\n\n"
            "Use value, ignore unused, and preserve missing values.\n\n"
            "Execution contract: no network.\n\nMandatory output files:\n"
            "- `summary.json` (finite JSON; include row count)\n"
        )

    def test_preserves_all_original_requirements_and_annotations(self):
        prompt, metadata = render_prompt(self.case)
        text = prompt.decode()
        self.assertTrue(all(text.count(h + "\n") == 1 for h in HEADINGS))
        self.assertIn("Use value, ignore unused, and preserve missing values.", text)
        self.assertIn("`summary.json` (finite JSON; include row count)", text)
        self.assertEqual(metadata["case_id"], "001_example")

    def test_renders_headers_without_reference_graph_or_data_values(self):
        prompt, _ = render_prompt(self.case)
        self.assertIn(b"Columns present: id, value, unused", prompt)
        self.assertNotIn(b"1,2,3", prompt)
        self.assertIn(b"not a requirement to use every column", prompt)
        # A private graph must not affect the generated task prompt.
        (self.case / "task_graph.json").write_text('{"secret": "ORACLE_SENTINEL"}')
        self.assertEqual(prompt, render_prompt(self.case)[0])

    def test_stale_source_or_header_invalidates_publication(self):
        sync_prompts(self.root)
        sync_prompts(self.root, check=True)
        (self.case / "inputs" / "data.csv").write_text("id,new_column\n1,2\n")
        with self.assertRaisesRegex(ValueError, "stale"):
            sync_prompts(self.root, check=True)
        sync_prompts(self.root)
        self.assertIn("new_column", (self.case / "prompt.txt").read_text())
        description = self.case / "description.md"
        description.write_text(description.read_text().replace("no network", "no network or shell"))
        with self.assertRaisesRegex(ValueError, "stale"):
            sync_prompts(self.root, check=True)

    def test_mirrors_and_hash_manifest(self):
        corpus = self.root / "corpus"
        (corpus / "cases" / self.case.name).mkdir(parents=True)
        sync_prompts(self.root, corpus)
        self.assertEqual((self.case / "prompt.txt").read_bytes(),
                         (corpus / "cases" / self.case.name / "prompt.txt").read_bytes())
        manifest = json.loads((corpus / "prompt-manifest.json").read_text())
        self.assertEqual(manifest["case_count"], 1)
        self.assertEqual(manifest["cases"][0]["prompt_sha256"], render_prompt(self.case)[1]["prompt_sha256"])

    def test_missing_output_section_fails_before_publication(self):
        (self.case / "description.md").write_text("# Example\n\nBuild a pipeline.")
        with self.assertRaisesRegex(ValueError, "Missing mandatory output"):
            sync_prompts(self.root)
        self.assertFalse((self.case / "prompt.txt").exists())


if __name__ == "__main__":
    unittest.main()
