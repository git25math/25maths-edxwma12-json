#!/usr/bin/env python3
"""Step 4: Validate all tags against syllabus."""

import json
import glob
from pathlib import Path

ROOT = Path("/Users/zhuxingzhe/Project/ExamBoard/25maths-edxwma12-json")


def main():
    syllabus = json.load(open(ROOT / "syllabus-wma12.json"))
    valid_sections = set()
    for ch in syllabus["chapters"]:
        for s in ch["sections"]:
            valid_sections.add(s["id"])

    qp_files = sorted(glob.glob(str(ROOT / "*/WMA*/*.json")))
    qp_files = [f for f in qp_files if not f.endswith("-ms.json") and not f.endswith(".raw") and "progress" not in f and "syllabus" not in f]

    errors = []
    warnings = []
    total_qs = 0
    tagged_qs = 0

    for f in qp_files:
        d = json.load(open(f))
        paper = d.get("paper", "")
        for q in d.get("questions", []):
            total_qs += 1
            qid = f"{paper}-Q{q['qnum']}"
            meta = q.get("meta", {})

            # Check 1: meta not empty
            sections = meta.get("sections", [])
            if not sections:
                errors.append(f"{qid}: empty sections")
                continue
            tagged_qs += 1

            # Check 2: valid section IDs
            for s in sections:
                if s not in valid_sections and s != "P1":
                    errors.append(f"{qid}: invalid section '{s}' (valid: {sorted(valid_sections)})")

            # Check 3: primary in sections
            primary = meta.get("primary_section", "")
            if primary and primary not in sections:
                errors.append(f"{qid}: primary '{primary}' not in sections {sections}")

            # Check 4: section count 1-3
            if len(sections) > 3:
                warnings.append(f"{qid}: {len(sections)} sections (expected 1-3)")

            # Check 5: cognitive level
            cl = meta.get("cognitive_level", "")
            if cl not in ("AO1", "AO2", "AO3"):
                warnings.append(f"{qid}: cognitive_level='{cl}' (expected AO1/AO2/AO3)")

            # Check 6: command words
            cw = meta.get("command_words", [])
            if not cw:
                warnings.append(f"{qid}: empty command_words")

    # Check 7: section distribution
    from collections import Counter
    section_counts = Counter()
    for f in qp_files:
        d = json.load(open(f))
        for q in d.get("questions", []):
            for s in q.get("meta", {}).get("sections", []):
                section_counts[s] += 1

    empty_sections = [s for s in sorted(valid_sections) if section_counts.get(s, 0) == 0]
    if empty_sections:
        warnings.append(f"Sections with 0 questions: {empty_sections}")

    # Report
    print(f"{'=' * 60}")
    print(f"WMA12 Tag Validation Report")
    print(f"{'=' * 60}")
    print(f"  Total questions: {total_qs}")
    print(f"  Tagged: {tagged_qs}")
    print(f"  Coverage: {tagged_qs * 100 // max(total_qs, 1)}%")
    print(f"  ❌ Errors: {len(errors)}")
    print(f"  ⚠ Warnings: {len(warnings)}")

    if errors:
        print(f"\n  ❌ ERRORS:")
        for e in errors:
            print(f"    {e}")

    if warnings:
        print(f"\n  ⚠ WARNINGS:")
        for w in warnings:
            print(f"    {w}")

    print(f"\n  Section distribution:")
    for s in sorted(valid_sections):
        c = section_counts.get(s, 0)
        bar = "█" * (c // 2)
        print(f"    {s:4s} {c:3d} {bar}")

    if not errors:
        print(f"\n  🎉 VALIDATION PASSED")
    else:
        print(f"\n  ⚠ {len(errors)} errors need fixing")

    # Save report
    report = {
        "total": total_qs, "tagged": tagged_qs, "errors": len(errors),
        "warnings": len(warnings), "section_counts": dict(section_counts),
        "error_details": errors, "warning_details": warnings,
    }
    with open(ROOT / "data" / "validation_report.json", "w") as f:
        json.dump(report, f, indent=2)


if __name__ == "__main__":
    main()
