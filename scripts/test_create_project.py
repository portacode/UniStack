"""Verify project ownership changes using disposable Git repositories."""

import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest


spec = importlib.util.spec_from_file_location("create_project", Path(__file__).with_name("create_project.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def run(path, *args):
    return subprocess.check_output(["git", "-C", str(path), *args], stderr=subprocess.PIPE, text=True).strip()


class ProjectOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="unistack-project-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.home = self.base / "home"
        self.home.mkdir()
        self.source = self.home / ".unistack-template"

    def repository(self, name):
        path = self.base / name
        path.mkdir()
        run(path, "init", "-q")
        run(path, "config", "user.name", "Template Test")
        run(path, "config", "user.email", "template@example.invalid")
        (path / "README.md").write_text(name)
        run(path, "add", "README.md")
        run(path, "commit", "-qm", "Fixture")
        return path

    def clone(self):
        leaf = self.repository("leaf")
        child = self.repository("child")
        run(child, "-c", "protocol.file.allow=always", "submodule", "add", "-q", str(leaf), "nested")
        run(child, "commit", "-qam", "Nested fixture")
        parent = self.repository("parent")
        for name in ("unicom", "unibot"):
            run(parent, "-c", "protocol.file.allow=always", "submodule", "add", "-q", str(child), f"apps/{name}")
        (parent / "apps" / "unicrm").mkdir()
        (parent / "apps" / "unicrm" / "snapshot.txt").write_text("retained CRM")
        run(parent, "add", ".")
        run(parent, "commit", "-qm", "Parent fixture")
        subprocess.run(["git", "-c", "protocol.file.allow=always", "clone", "-q", "--recurse-submodules", str(parent), str(self.source)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return child, leaf

    def test_rename_detaches_parent_and_preserves_nested_git_history(self):
        child, leaf = self.clone()
        target = module.prepare_project(self.source, self.home, "new-app")
        self.assertEqual(target, self.home / "new-app")
        self.assertFalse(self.source.exists())
        self.assertFalse((target / ".git").exists())
        self.assertTrue((target / ".gitmodules").is_file())
        for name in ("unicom", "unibot"):
            for suffix, original in (("", child), ("/nested", leaf)):
                repo = target / f"apps/{name}{suffix}"
                self.assertTrue((repo / ".git").is_dir())
                self.assertEqual(run(repo, "rev-parse", "HEAD"), run(original, "rev-parse", "HEAD"))
                self.assertEqual(run(repo, "status", "--porcelain"), "")
                self.assertEqual(Path(run(repo, "rev-parse", "--show-toplevel")), repo)
                self.assertEqual(run(repo, "remote", "get-url", "origin"), str(original))
        self.assertEqual((target / "apps/unicrm/snapshot.txt").read_text(), "retained CRM")

    def test_default_name(self):
        self.clone()
        self.assertEqual(module.prepare_project(self.source, self.home, "").name, "my-project")

    def test_rejects_existing_destination_before_changing_git(self):
        self.clone()
        (self.home / "existing").mkdir()
        with self.assertRaisesRegex(ValueError, "already exists"):
            module.prepare_project(self.source, self.home, "existing")
        self.assertTrue((self.source / ".git").is_dir())
        self.assertTrue((self.source / "apps/unicom/.git").is_file())

    def test_rejects_unsafe_slug(self):
        for slug in ("../other", "/tmp/other", "hello world", "$(id)", "A", "a--b", " a ", "a" * 64):
            with self.subTest(slug=slug), self.assertRaises(ValueError):
                module.prepare_project(self.source, self.home, slug)

    def test_refuses_to_detach_an_existing_checkout(self):
        parent = self.repository("real-project")
        with self.assertRaisesRegex(ValueError, "fresh"):
            module.prepare_project(parent, self.home, "new-app")
        self.assertTrue((parent / ".git").is_dir())


if __name__ == "__main__":
    unittest.main()
