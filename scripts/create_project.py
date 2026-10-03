"""Turn a freshly cloned template into a named project owned by its deployer."""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess


def git(path, *args):
    return subprocess.check_output(["git", "-C", str(path), *args], text=True).strip()


def prepare_project(source, home, slug):
    source, home = Path(source).resolve(), Path(home).resolve()
    slug = slug or "my-project"
    if not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", slug) or len(slug) > 63:
        raise ValueError("Project slug must be 1–63 lowercase letters, numbers, or single hyphens, starting with a letter")
    target = home / slug
    if target.exists() or target.is_symlink():
        raise ValueError(f"Project folder already exists: {target}")
    if source.parent != home or source.name != ".unistack-template" or not (source / ".git").is_dir():
        raise ValueError("Only a fresh home/.unistack-template clone can be detached")
    parent_git = source / ".git"
    children = []
    # Collect every gitdir before moving any: nested submodules may share storage
    # below their parent's gitdir. Move deepest repositories first.
    paths = git(source, "submodule", "foreach", "--quiet", "--recursive", "pwd").splitlines()
    for raw_path in paths:
        child = Path(raw_path).resolve()
        child.relative_to(source)
        gitdir = Path(git(child, "rev-parse", "--absolute-git-dir")).resolve()
        gitdir.relative_to(parent_git)
        if not (child / ".git").is_file():
            raise ValueError(f"Expected a freshly cloned submodule: {child}")
        children.append((child, gitdir, git(child, "rev-parse", "HEAD")))
    provenance = {str(child.relative_to(source)): commit for child, _, commit in children}
    for child, gitdir, commit in sorted(children, key=lambda item: len(item[0].parts), reverse=True):
        (child / ".git").unlink()
        shutil.move(str(gitdir), str(child / ".git"))
        subprocess.run(["git", "config", "--file", str(child / ".git/config"), "--unset-all", "core.worktree"], check=True)
        if git(child, "rev-parse", "HEAD") != commit or Path(git(child, "rev-parse", "--show-toplevel")).resolve() != child:
            raise RuntimeError(f"Child repository could not be preserved: {child}")
    # Verify before removing the parent history. Existing child .git directories
    # (including any bundled repositories) are not part of this deletion.
    (source / ".template-origin.json").write_text(json.dumps({
        "template": "portacode/UniStack", "commit": git(source, "rev-parse", "HEAD"),
        "project_slug": slug, "children": provenance,
    }, indent=2) + "\n")
    shutil.rmtree(parent_git)
    source.rename(target)
    for relative, commit in provenance.items():
        if git(target / relative, "rev-parse", "HEAD") != commit:
            raise RuntimeError(f"Child repository changed during rename: {relative}")
    return target


if __name__ == "__main__":
    try:
        project = prepare_project(Path(__file__).resolve().parent.parent, Path.home(), os.environ.get("PROJECT_SLUG", ""))
        print(f"Project created: {project}")
    except (ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error))
