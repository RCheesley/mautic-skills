#!/usr/bin/env python3
"""Check that every [PR #N] tag in skills/ is a merged pull request on mautic/mautic.

Usage: check-pr-tags.py [--cache FILE] [--refresh] [skills_dir]
The list of merged PR numbers is fetched with `gh api graphql` (numbers only, 100 per call) and cached in FILE
(default: .cache/merged-pr-numbers.txt, git-ignored). Exits 1 if any tag is not a merged PR, and prints each one.
Issue numbers should be written as "issue mautic/mautic#N", without the [PR] tag.
"""
import json, os, re, subprocess, sys

args = [x for x in sys.argv[1:] if not x.startswith("--")]
cache = sys.argv[sys.argv.index("--cache") + 1] if "--cache" in sys.argv else os.path.join(
    os.path.dirname(__file__), "..", ".cache", "merged-pr-numbers.txt")
if "--cache" in sys.argv:
    args.remove(cache)
root = args[0] if args else os.path.join(os.path.dirname(__file__), "..", "skills")

Q = """query($c: String) { repository(owner: "mautic", name: "mautic") {
  pullRequests(states: MERGED, first: 100, after: $c) { pageInfo { hasNextPage endCursor } nodes { number } } } }"""

if "--refresh" in sys.argv or not os.path.exists(cache):
    nums, cur = [], None
    while True:
        cmd = ["gh", "api", "graphql", "-f", f"query={Q}"] + (["-f", f"c={cur}"] if cur else [])
        d = json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)
        p = d["data"]["repository"]["pullRequests"]
        nums += [n["number"] for n in p["nodes"]]
        if not p["pageInfo"]["hasNextPage"]:
            break
        cur = p["pageInfo"]["endCursor"]
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    open(cache, "w").write("\n".join(map(str, sorted(nums))) + "\n")

merged = {int(x) for x in open(cache).read().split()}
bad, total = [], 0
for d, _, files in os.walk(root):
    for fn in files:
        if fn.endswith(".md"):
            fp = os.path.join(d, fn)
            for i, line in enumerate(open(fp, encoding="utf-8"), 1):
                for n in re.findall(r"\[PR #(\d+)\]", line):
                    total += 1
                    if int(n) not in merged:
                        bad.append(f"{os.path.relpath(fp, root)}:{i}: [PR #{n}]")
print(f"{total} PR tags checked against {len(merged)} merged PRs; {len(bad)} not merged")
for b in bad:
    print("  " + b)
sys.exit(1 if bad else 0)
