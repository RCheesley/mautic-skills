#!/usr/bin/env python3
"""Move `[code: path:lines @TAG]` citations from an old snapshot to a new one.

Usage:
  remap-code-citations.py --repo MAUTIC_CHECKOUT --old OLD_SHA --new NEW_REF --tag 7.x [--apply] [--report OUT.tsv] [skills_dir]

For every citation with the given tag, the script follows the git history between OLD and NEW for that file:
  unchanged  the cited lines are identical and did not move
  shifted    the cited lines are identical but moved; --apply rewrites the line numbers
  renamed    the file moved (and the lines are identical); --apply rewrites the path and numbers
  changed    at least one cited line was edited or removed; needs a human or agent to re-check the claim
  deleted    the file no longer exists at NEW; needs re-checking
  nolines    the citation names a file without line numbers; only existence is checked
Changed and deleted citations are never moved. With --pin-changed, their tag is replaced by the old commit
(for example `@7.x` becomes `@419a08a9b35`), so each citation stays true until someone re-checks it and moves it
back to the moving tag. The TSV report lists every citation with its status.
"""
import argparse, collections, os, re, subprocess, sys

CITE = re.compile(r"\[code: ([A-Za-z0-9_.*/@-][A-Za-z0-9_.*/@ -]*?)(?::([0-9][0-9, -]*[0-9]))? @(%s)\]")


def git(repo, *args):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def parse_ranges(spec):
    out = []
    for part in spec.replace(" ", "").split(","):
        if not part:
            continue
        a, _, b = part.partition("-")
        a = int(a); b = int(b) if b else a
        out.append((a, max(a, b)))
    return out


class FileMap:
    """Line mapping for one file between OLD and NEW, built from a zero-context diff."""

    def __init__(self, repo, old, new, path, renames):
        self.path = path
        self.new_path = renames.get(path, path)
        self.exists_old = git(repo, "cat-file", "-e", f"{old}:{path}") is not None
        self.exists_new = git(repo, "cat-file", "-e", f"{new}:{self.new_path}") is not None
        self.hunks = []  # (old_start, old_count, new_start, new_count)
        if self.exists_old and self.exists_new:
            d = git(repo, "diff", "-U0", "--no-color", f"{old}:{path}", f"{new}:{self.new_path}") or ""
            for m in re.finditer(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", d, re.M):
                os_, oc, ns, nc = int(m[1]), int(m[2] or 1), int(m[3]), int(m[4] or 1)
                self.hunks.append((os_, oc, ns, nc))

    def map_line(self, n):
        """Return the new line number for old line n, or None if line n was edited or removed."""
        offset = 0
        for os_, oc, ns, nc in self.hunks:
            if oc == 0:  # pure insertion after old line os_
                if os_ < n:
                    offset += nc
                continue
            if n < os_:
                break
            if os_ <= n < os_ + oc:
                return None
            offset += nc - oc
        return n + offset


def fmt_ranges(ranges):
    return ",".join(f"{a}" if a == b else f"{a}-{b}" for a, b in ranges)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--old", required=True)
    ap.add_argument("--new", required=True)
    ap.add_argument("--tag", required=True, help="citation tag without @, e.g. 7.x")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--pin-changed", action="store_true", help="retag changed/deleted citations to @OLD")
    ap.add_argument("--report")
    ap.add_argument("skills", nargs="?", default=os.path.join(os.path.dirname(__file__), "..", "skills"))
    a = ap.parse_args()

    cite = re.compile(CITE.pattern % re.escape(a.tag))
    renames = {}
    for line in (git(a.repo, "diff", "-M", "--name-status", a.old, a.new) or "").splitlines():
        parts = line.split("\t")
        if parts[0].startswith("R") and len(parts) == 3:
            renames[parts[1]] = parts[2]

    maps, stats, rows = {}, collections.Counter(), []
    for root, _, files in os.walk(a.skills):
        for fn in sorted(files):
            if not fn.endswith(".md"):
                continue
            fp = os.path.join(root, fn)
            text = open(fp, encoding="utf-8").read()
            out, pos, changed_file = [], 0, False
            for m in cite.finditer(text):
                path, spec = m.group(1).strip(), m.group(2)
                lineno = text.count("\n", 0, m.start()) + 1
                if "*" in path or " " in path:
                    stats["skipped"] += 1
                    continue
                fm = maps.get(path) or maps.setdefault(path, FileMap(a.repo, a.old, a.new, path, renames))
                new_text = m.group(0)
                if not fm.exists_old and not fm.exists_new:
                    status = "missing"
                elif not fm.exists_new:
                    status = "deleted"
                elif spec is None:
                    status = "nolines" if fm.new_path == path else "renamed"
                    if status == "renamed":
                        new_text = f"[code: {fm.new_path} @{a.tag}]"
                else:
                    new_ranges, ok = [], True
                    for s, e in parse_ranges(spec):
                        mapped = [fm.map_line(n) for n in range(s, e + 1)]
                        if any(x is None for x in mapped) or mapped != list(range(mapped[0], mapped[0] + len(mapped))):
                            ok = False
                            break
                        new_ranges.append((mapped[0], mapped[-1]))
                    if not ok:
                        status = "changed"
                    else:
                        new_spec = fmt_ranges(new_ranges)
                        if fm.new_path != path:
                            status = "renamed"
                        elif new_spec != fmt_ranges(parse_ranges(spec)):
                            status = "shifted"
                        else:
                            status = "unchanged"
                        new_text = f"[code: {fm.new_path}:{new_spec} @{a.tag}]"
                stats[status] += 1
                rows.append((os.path.relpath(fp, a.skills), lineno, status, m.group(0), new_text))
                if a.apply and a.pin_changed and status in ("changed", "deleted"):
                    new_text = m.group(0)[: -len(f"@{a.tag}]")] + f"@{a.old}]"
                if a.apply and status in ("shifted", "renamed", "changed", "deleted") and new_text != m.group(0):
                    out.append(text[pos:m.start()]); out.append(new_text); pos = m.end(); changed_file = True
            if a.apply and changed_file:
                out.append(text[pos:])
                open(fp, "w", encoding="utf-8").write("".join(out))

    if a.report:
        with open(a.report, "w") as f:
            f.write("skill_file\tline\tstatus\tcitation\tnew_citation\n")
            for r in rows:
                f.write("\t".join(map(str, r)) + "\n")
    total = sum(stats.values())
    print(f"@{a.tag}: {total} citations, " + ", ".join(f"{k} {v}" for k, v in stats.most_common()))
    print("applied" if a.apply else "dry run (use --apply to rewrite shifted and renamed citations)")


if __name__ == "__main__":
    main()
