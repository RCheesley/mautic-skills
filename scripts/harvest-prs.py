#!/usr/bin/env python3
"""Harvest every merged PR on mautic/mautic via GitHub GraphQL into JSONL.
Resumable: reads cursor from state file. Handles rate limits by sleeping."""
import json, subprocess, sys, time, os

OUT_DIR = sys.argv[1]
JSONL = os.path.join(OUT_DIR, "merged_prs.jsonl")
STATE = os.path.join(OUT_DIR, "cursor.json")
LOG = os.path.join(OUT_DIR, "fetch.log")

QUERY = """
query($cursor: String) {
  rateLimit { cost remaining resetAt }
  repository(owner: "mautic", name: "mautic") {
    pullRequests(states: MERGED, first: 50, after: $cursor, orderBy: {field: CREATED_AT, direction: ASC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number title body url state createdAt mergedAt closedAt
        baseRefName headRefName additions deletions changedFiles
        author { login }
        mergedBy { login }
        milestone { title }
        labels(first: 20) { nodes { name } }
        files(first: 40) { nodes { path additions deletions } }
        comments(first: 40) { totalCount nodes { author { login } createdAt body } }
        reviews(first: 10) { totalCount nodes { author { login } state submittedAt body } }
        closingIssuesReferences(first: 10) { nodes { number title } }
      }
    }
  }
}
"""

def log(msg):
    with open(LOG, "a") as f:
        f.write(time.strftime("%H:%M:%S ") + msg + "\n")

cursor = None
if os.path.exists(STATE):
    cursor = json.load(open(STATE)).get("cursor")
    log(f"resuming from cursor {cursor}")

page = 0
while True:
    args = ["gh", "api", "graphql", "-f", f"query={QUERY}"]
    if cursor:
        args += ["-f", f"cursor={cursor}"]
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        log(f"error: {r.stderr[:500]} {r.stdout[:500]}")
        if "RATE_LIMITED" in r.stdout or "rate limit" in r.stderr.lower() or "403" in r.stderr:
            log("rate limited; sleeping 600s"); time.sleep(600); continue
        time.sleep(30); continue
    data = json.loads(r.stdout)
    if "errors" in data and not data.get("data"):
        log(f"graphql errors: {json.dumps(data['errors'])[:500]}"); time.sleep(60); continue
    rl = data["data"]["rateLimit"]
    prs = data["data"]["repository"]["pullRequests"]
    with open(JSONL, "a") as f:
        for n in prs["nodes"]:
            f.write(json.dumps(n) + "\n")
    page += 1
    cursor = prs["pageInfo"]["endCursor"]
    json.dump({"cursor": cursor}, open(STATE, "w"))
    log(f"page {page} ok; {len(prs['nodes'])} prs; cost {rl['cost']} remaining {rl['remaining']} last #{prs['nodes'][-1]['number'] if prs['nodes'] else '-'}")
    if not prs["pageInfo"]["hasNextPage"]:
        log("DONE"); break
    if rl["remaining"] < 100:
        log("near limit; sleeping 900s"); time.sleep(900)
    time.sleep(1)
