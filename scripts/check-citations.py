#!/usr/bin/env python3
"""Report statements in skills/ that carry no source tag.

A "statement" is a bullet line or a numbered-list line in SKILL.md or references/*.md. Lines inside fenced code
blocks, table header/separator rows, headings, and navigation bullets (lines that only point to another skill or
reference file) are skipped. A statement is cited if it contains one of the tags defined in SOURCES.md.

Usage: scripts/check-citations.py [skills_dir] [--verbose]
Advisory by default. With --strict, exit 1 if any statement is uncited. List items that inherit a citation from a
lead-in line separated by a blank line are reported as uncited; review those by eye.
"""
import os
import re
import sys

TAG = re.compile(r"\[(code|docs|devdocs|kb|PR|unverified)\b|\[PR #|\(PR #")
STATEMENT = re.compile(r"^\s*(?:[-*]|\d+\.\d+\.?|\d+\.|[A-Z]{1,2}\d+(?:\.\d+)?[.):]?|[A-Z]\d+\s)\s+\S")
NAV = re.compile(r"^\s*[-*]\s+(?:`?(?:references/[\w-]+\.md|mautic-[\w-]+)`?)\s*(?:[—:-]|$)")


TOC = re.compile(r"^\s*(?:[-*]|\d+\.)\s+\[[^\]]+\]\(#[^)]*\)\s*$|^\s*\d+\.\s+[A-Z][^.\[]{0,60}$")


def statements(path):
    """Yield (line_no, text) for each statement, joining wrapped continuation lines."""
    in_code, cur, start = False, None, 0
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            if line.lstrip().startswith("```"):
                in_code = not in_code
                if cur is not None:
                    yield start, cur
                    cur = None
                continue
            if in_code:
                continue
            is_stmt = bool(STATEMENT.match(line))
            stripped = line.strip()
            # A sub-bullet (indented, or listed under a parent that ends with ':') belongs to its parent statement.
            is_sub = (is_stmt and cur is not None and stripped != ""
                      and (line[:1] in (" ", "\t") or cur.rstrip().endswith(":")))
            if is_sub:
                cur += " " + stripped
                continue
            is_cont = (not is_stmt and cur is not None and stripped != ""
                       and not stripped.startswith(("|", "#", "```")))
            if is_cont:
                cur += " " + line.strip()
                continue
            if cur is not None:
                yield start, cur
                cur = None
            if is_stmt and not NAV.match(line) and not TOC.match(line):
                cur, start = line.rstrip(), n
    if cur is not None:
        yield start, cur


def check_file(path):
    uncited, total = [], 0
    for n, text in statements(path):
        total += 1
        if not TAG.search(text):
            uncited.append((n, text))
    return total, uncited


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    verbose = "--verbose" in sys.argv
    root = args[0] if args else os.path.join(os.path.dirname(__file__), "..", "skills")
    grand_total = grand_uncited = 0
    for skill in sorted(os.listdir(root)):
        sdir = os.path.join(root, skill)
        if not os.path.isdir(sdir):
            continue
        files = [os.path.join(sdir, "SKILL.md")]
        rdir = os.path.join(sdir, "references")
        if os.path.isdir(rdir):
            files += sorted(os.path.join(rdir, f) for f in os.listdir(rdir) if f.endswith(".md"))
        s_total = s_uncited = 0
        for f in files:
            if not os.path.exists(f):
                continue
            total, uncited = check_file(f)
            s_total += total
            s_uncited += len(uncited)
            if verbose:
                for n, text in uncited:
                    print(f"  {os.path.relpath(f, root)}:{n}: {text[:140]}")
        pct = 100.0 * (s_total - s_uncited) / s_total if s_total else 100.0
        print(f"{skill:40s} statements {s_total:5d}  uncited {s_uncited:4d}  cited {pct:5.1f}%")
        grand_total += s_total
        grand_uncited += s_uncited
    pct = 100.0 * (grand_total - grand_uncited) / grand_total if grand_total else 100.0
    print(f"{'TOTAL':40s} statements {grand_total:5d}  uncited {grand_uncited:4d}  cited {pct:5.1f}%")
    sys.exit(1 if (grand_uncited and "--strict" in sys.argv) else 0)


if __name__ == "__main__":
    main()
