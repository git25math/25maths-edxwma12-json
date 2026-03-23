#!/usr/bin/env python3
"""Step 3: Merge Gemini tags back into QP JSON meta fields."""

import json
import glob
import shutil
from datetime import date
from pathlib import Path

ROOT = Path("/Users/zhuxingzhe/Project/ExamBoard/25maths-edxwma12-json")
TAGGED = ROOT / "data" / "tagged_results.json"


def main():
    tagged = json.load(open(TAGGED))
    results = tagged.get("results", [])

    # Index by id
    tag_map = {}
    for r in results:
        tag_map[r["id"]] = r

    print(f"Loaded {len(tag_map)} tagged results")

    # Find all QP files
    qp_files = sorted(glob.glob(str(ROOT / "*/WMA*/*.json")))
    qp_files = [f for f in qp_files if not f.endswith("-ms.json") and not f.endswith(".raw") and "progress" not in f and "syllabus" not in f]

    merged = 0
    missing = 0

    for f in qp_files:
        d = json.load(open(f))
        paper = d.get("paper", "")
        changed = False

        for q in d.get("questions", []):
            qid = f"{paper}-Q{q['qnum']}"
            tag = tag_map.get(qid)

            if tag:
                q["meta"] = {
                    "sections": tag.get("sections", []),
                    "primary_section": tag.get("primary_section", ""),
                    "question_type": tag.get("question_type", ""),
                    "command_words": tag.get("command_words", []),
                    "cognitive_level": tag.get("cognitive_level", ""),
                    "tagged_at": str(date.today()),
                    "tagger": "gemini-2.5-flash",
                }
                merged += 1
                changed = True
            else:
                print(f"  ⚠ No tag for {qid}")
                missing += 1

        if changed:
            # Backup
            bak = f + ".bak"
            shutil.copy2(f, bak)
            # Write
            with open(f, "w") as fh:
                json.dump(d, fh, ensure_ascii=False, indent=2)
                fh.write("\n")

    print(f"\n✅ Merged: {merged} questions")
    if missing:
        print(f"⚠ Missing: {missing} questions")
    else:
        print(f"✅ No missing tags — 100% coverage")


if __name__ == "__main__":
    main()
