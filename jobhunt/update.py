"""Preview an update from the main project before taking it. Read-only; no AI calls.

People change their copy: a prompt reworded, the resume template restyled, a
rule added to AGENTS.md. Taking the latest version can then clash with those
edits. This shows, before anything changes:

- the new commits, sorted into "worth reviewing" (they change how agents or
  scripts behave) and "probably skip" (docs, tests, CI)
- the files the update changes that you changed too, which are the ones to
  check after merging

It never merges, pulls or resets. `private/` is never in git, so an update
can't touch your profile, tracker or applications.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

# Paths whose changes alter what agents or scripts do.
BEHAVIOUR = ("jobhunt/", "prompts/", "AGENTS.md", "CLAUDE.md", "MODES.md", "resume/", "sheet/",
             "scripts/", "examples/", "requirements.txt")
# Paths that only explain or test.
QUIET = ("README.md", "GUIDE.md", "START-HERE.md", "tests/", ".github/", "LICENSE", ".gitignore")


class UpdateError(RuntimeError):
    pass


@dataclass
class Preview:
    target: str
    commits: list[tuple[str, str, list[str]]] = field(default_factory=list)   # (sha, subject, files)
    changed_upstream: list[str] = field(default_factory=list)
    changed_here: list[str] = field(default_factory=list)

    @property
    def both(self) -> list[str]:
        mine = set(self.changed_here)
        return [f for f in self.changed_upstream if f in mine]

    def worth_reviewing(self) -> list[tuple[str, str, list[str]]]:
        return [c for c in self.commits if kind(c[2]) == "review"]

    def probably_skip(self) -> list[tuple[str, str, list[str]]]:
        return [c for c in self.commits if kind(c[2]) == "skip"]


def kind(files: list[str]) -> str:
    """'review' if any file changes behaviour (or is unknown), 'skip' if all only explain or test."""
    if files and all(f.startswith(QUIET) for f in files):
        return "skip"
    return "review"


def _git(repo: Path, *args: str) -> str:
    try:
        out = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=120)
    except FileNotFoundError:
        raise UpdateError("git isn't installed") from None
    except subprocess.TimeoutExpired:
        raise UpdateError(f"git {args[0]} took too long; check your internet connection") from None
    if out.returncode:
        raise UpdateError((out.stderr or out.stdout).strip().splitlines()[-1] if (out.stderr or out.stdout).strip()
                          else f"git {args[0]} failed")
    return out.stdout


def _lines(s: str) -> list[str]:
    return [ln.strip() for ln in s.splitlines() if ln.strip()]


def pick_remote(repo: Path) -> str:
    """'upstream' when you cloned your own copy and added the project as upstream, else 'origin'."""
    remotes = _lines(_git(repo, "remote"))
    if not remotes:
        raise UpdateError("this folder has no git remote. Add the project with: "
                          "git remote add upstream https://github.com/josephfanpm/agentic-job-hunt.git")
    return "upstream" if "upstream" in remotes else "origin" if "origin" in remotes else remotes[0]


def preview(repo: Path, remote: str | None = None, branch: str = "main", fetch: bool = True) -> Preview:
    repo = Path(repo)
    if _git(repo, "rev-parse", "--is-inside-work-tree").strip() != "true":
        raise UpdateError("this folder isn't a git copy of the project")
    remote = remote or pick_remote(repo)
    if fetch:
        _git(repo, "fetch", "--quiet", remote, branch)
    target = f"{remote}/{branch}"
    base = _git(repo, "merge-base", "HEAD", target).strip()
    p = Preview(target=target)
    for line in _lines(_git(repo, "log", "--reverse", "--format=%h%x09%s", f"HEAD..{target}")):
        sha, _, subject = line.partition("\t")
        files = _lines(_git(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", sha))
        p.commits.append((sha, subject, files))
    p.changed_upstream = _lines(_git(repo, "diff", "--name-only", base, target))
    here = set(_lines(_git(repo, "diff", "--name-only", base, "HEAD")))
    for line in _git(repo, "status", "--porcelain").splitlines():
        if len(line) > 3:
            here.add(line[3:].split(" -> ")[-1].strip().strip('"'))
    p.changed_here = sorted(here)
    return p


def render(p: Preview) -> str:
    if not p.commits:
        return f"Up to date with {p.target}."
    out = [f"{len(p.commits)} new commit(s) on {p.target}."]
    review, skip = p.worth_reviewing(), p.probably_skip()
    if review:
        out.append("\nWorth reviewing (they change how agents or scripts behave):")
        out += [f"  {sha}  {subject}" for sha, subject, _ in review]
    if skip:
        out.append("\nProbably skip (docs, tests or CI only):")
        out += [f"  {sha}  {subject}" for sha, subject, _ in skip]
    both = p.both
    if both:
        out.append("\nYou changed these files too. Check them after merging; git stops and asks if the edits clash:")
        out += [f"  {f}" for f in both]
    else:
        out.append("\nNone of the files it changes were changed here, so it should merge cleanly.")
    out.append(f"\nTo take the update: git merge {p.target}   (private/ is never touched)")
    return "\n".join(out)
