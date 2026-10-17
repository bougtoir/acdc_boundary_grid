#!/usr/bin/env python3
"""AST + regex numeric literal inventory for the hardcode audit (Phase 2).

Scans all executable and generative files. Classifies each numeric literal:
A algorithmic (0,1,small ints, indices, loop bounds, math definitions)
B documented engineering constant (units/source in context)
C declared scenario/config parameter
D test-only synthetic fixture
E forbidden embedded empirical result / manuscript scalar / count / percentage
F suspicious, needs human interpretation
"""
import ast
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "numeric_literal_inventory.csv"

SCAN_GLOBS = ["**/*.py", "**/*.yaml", "**/*.yml", "**/*.toml", "**/*.cfg", "Makefile", "**/*.md", "**/*.txt"]
SKIP_DIRS = {".venv", ".git", "data_raw", "data_interim", "data_processed", "__pycache__",
             "tsg_submission_package", "build", "figures", "node_modules", ".pytest_cache"}
SKIP_FILES = {"numeric_literal_inventory.csv", "numeric_literal_scan.py",
              "baseline_manifest_adversarial.txt"}
RESULTS_FILES = set()  # results/tables are generated outputs, scanned only via producers

ALGO_OK = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 100, 1000, -1}
NUMERIC_IN_STRING = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?(?:e[+-]?\d+)?)(?![\w%])", re.I)


def classify(file: Path, line: str, literal: float, in_string: bool) -> tuple[str, str]:
    rel = file.relative_to(ROOT).as_posix()
    s = line.lower()
    if rel.startswith("tests/"):
        return "D", "test fixture"
    if "configs/" in rel:
        return "C", "declared configuration parameter"
    if any(k in s for k in ("sha256", "doi", "url", "version", "year")):
        return "B", "provenance/publication metadata"
    if any(k in s for k in ("seed", "_seeds")):
        return "C", "frozen seed list (config-mirrored)"
    if rel.startswith("src/acdc_boundary/manuscript"):
        # numbers inside manuscript-generating literals
        if literal in (8.5, 11, 0.67, 240, 3.1, 3.0, 2.9, 10, 18, 8, 11, 0.12, 0.25):
            return "B", "layout/format constant"
        if in_string:
            return "E", "numeric literal embedded in manuscript prose/table code"
        return "F", "literal in document generator"
    if rel.startswith("src/acdc_boundary/pipeline"):
        if "novelty" in s:
            return "F", "hand-coded literature comparison flag"
        if in_string and literal not in ALGO_OK:
            return "E", "numeric literal embedded in generated report text"
        return "A" if literal in ALGO_OK else "F", "pipeline literal"
    if rel.startswith(("qc/", "reports/", "handoffs/", "provenance/")):
        return "F", "report/documentation literal (verify against registry)"
    if literal in ALGO_OK:
        return "A", "algorithmic literal"
    if in_string:
        return "F", "numeric literal inside string"
    return "F", "unclassified literal"


def iter_files():
    seen = set()
    for pattern in SCAN_GLOBS:
        for path in ROOT.rglob(pattern):
            if not path.is_file() or path in seen or path.name in SKIP_FILES:
                continue
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            seen.add(path)
            yield path


def scan_python(path: Path, rows):
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception:
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            line = lines[node.lineno - 1] if node.lineno - 1 < len(lines) else ""
            cls, note = classify(path, line, float(node.value), in_string=False)
            rows.append((path.relative_to(ROOT).as_posix(), node.lineno, node.value, "ast", line.strip()[:80], cls, note))
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            for m in NUMERIC_IN_STRING.finditer(node.value):
                line = lines[node.lineno - 1] if node.lineno - 1 < len(lines) else ""
                cls, note = classify(path, node.value[:120], float(m.group(1)), in_string=True)
                if cls in ("E", "F"):
                    rows.append((path.relative_to(ROOT).as_posix(), node.lineno, m.group(1), "str", node.value.strip()[:80], cls, note))


def scan_text(path: Path, rows):
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return
    for i, line in enumerate(lines, start=1):
        for m in NUMERIC_IN_STRING.finditer(line):
            cls, note = classify(path, line, float(m.group(1)), in_string=True)
            if cls in ("E", "F"):
                rows.append((path.relative_to(ROOT).as_posix(), i, m.group(1), "text", line.strip()[:80], cls, note))


def main():
    rows = []
    for path in sorted(iter_files()):
        if path.suffix == ".py":
            scan_python(path, rows)
        else:
            scan_text(path, rows)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["file", "line", "literal", "mode", "context", "classification", "provenance_or_decision", "remediation"])
        for r in rows:
            writer.writerow([*r, ""])
    from collections import Counter
    counts = Counter(r[5] for r in rows)
    print(dict(counts), "total", len(rows))
    for r in rows:
        if r[5] in ("E",):
            print("E:", r[0], r[1], r[2], "|", r[4])


if __name__ == "__main__":
    main()
