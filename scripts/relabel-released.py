#!/usr/bin/env python3
"""Report statements marked unreleased whose pull requests have since shipped in a release tag.

Usage: relabel-released.py --repo MAUTIC_CHECKOUT --tags 7.2.2[,7.3.0] [--report OUT.tsv] [skills_dir]

For every line in skills/ that says "unreleased" (any case) and carries [PR #N] tags, the script finds each PR's
merge commit on the upstream branches and checks whether it is contained in each given tag. Lines where every
tagged PR is now in a tag are candidates for relabelling; the wording is left to a human or agent, because the
phrasing of "unreleased" varies. Lines where only some PRs shipped are reported as partial.
"""
import argparse, collections, os, re, subprocess

PR = re.compile(r"\[PR #(\d+)\]")


def git(repo, *args):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--tags", required=True)
    ap.add_argument("--refs", default="upstream/7.x,upstream/7.2,upstream/8.x")
    ap.add_argument("--report")
    ap.add_argument("skills", nargs="?", default=os.path.join(os.path.dirname(__file__), "..", "skills"))
    a = ap.parse_args()
    tags = a.tags.split(",")

    merge = {}
    log = git(a.repo, "log", "--format=%H %s", *a.refs.split(","))
    for line in log.splitlines():
        sha, _, subj = line.partition(" ")
        m = re.match(r"Merge pull request #(\d+)", subj) or re.search(r"\(#(\d+)\)\s*$", subj)
        if m:
            merge.setdefault(int(m.group(1)), sha)

    cache = {}

    def released(n):
        if n not in cache:
            sha = merge.get(n)
            if not sha:
                cache[n] = None
            else:
                cache[n] = next((t for t in tags if subprocess.run(
                    ["git", "-C", a.repo, "merge-base", "--is-ancestor", sha, t]).returncode == 0), "")
        return cache[n]

    rows, stats = [], collections.Counter()
    for root, _, files in os.walk(a.skills):
        for fn in sorted(files):
            if not fn.endswith(".md"):
                continue
            fp = os.path.join(root, fn)
            for i, line in enumerate(open(fp, encoding="utf-8"), 1):
                if "unreleased" not in line.lower():
                    continue
                prs = sorted({int(x) for x in PR.findall(line)})
                if not prs:
                    stats["no-pr"] += 1
                    continue
                res = {n: released(n) for n in prs}
                shipped = [f"#{n}->{t}" for n, t in res.items() if t]
                unknown = [f"#{n}" for n, t in res.items() if t is None]
                if shipped and len(shipped) == len(prs):
                    status = "shipped"
                elif shipped:
                    status = "partial"
                elif unknown and len(unknown) == len(prs):
                    status = "unknown"
                else:
                    status = "still-unreleased"
                stats[status] += 1
                rows.append((os.path.relpath(fp, a.skills), i, status, " ".join(shipped), " ".join(unknown), line.strip()[:300]))
    if a.report:
        with open(a.report, "w") as f:
            f.write("skill_file\tline\tstatus\tshipped\tno_merge_commit_found\ttext\n")
            for r in rows:
                f.write("\t".join(map(str, r)) + "\n")
    print(", ".join(f"{k} {v}" for k, v in stats.most_common()))


if __name__ == "__main__":
    main()
