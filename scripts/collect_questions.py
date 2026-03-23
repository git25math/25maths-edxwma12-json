#!/usr/bin/env python3
"""Step 1: Collect all WMA12 questions into a flat JSON array for tagging."""

import json
import glob
from pathlib import Path

ROOT = Path("/Users/zhuxingzhe/Project/ExamBoard/25maths-edxwma12-json")
OUT = ROOT / "data" / "all_questions.json"


def extract_text(blocks):
    """Extract all text content from block arrays, preserving LaTeX."""
    texts = []
    for b in (blocks or []):
        if isinstance(b, dict):
            if b.get("type") == "text":
                texts.append(b.get("content", ""))
            elif b.get("type") == "table":
                texts.append(b.get("content", ""))
        elif isinstance(b, str):
            texts.append(b)
    return " ".join(texts)


def collect():
    qp_files = sorted(glob.glob(str(ROOT / "*/WMA*/*.json")))
    qp_files = [f for f in qp_files if not f.endswith("-ms.json") and not f.endswith(".raw") and "progress" not in f and "syllabus" not in f]

    all_qs = []
    for f in qp_files:
        d = json.load(open(f))
        paper = d.get("paper", "")
        for q in d.get("questions", []):
            qnum = q.get("qnum", 0)
            qid = f"{paper}-Q{qnum}"

            stem_text = extract_text(q.get("stem", []))

            parts_text = []
            for p in q.get("parts", []):
                label = p.get("label", "")
                content = extract_text(p.get("content", []))
                if p.get("subparts"):
                    for s in p["subparts"]:
                        sub_label = s.get("label", "")
                        sub_content = extract_text(s.get("content", []))
                        parts_text.append(f"{label}{sub_label} {sub_content}")
                else:
                    parts_text.append(f"{label} {content}")

            full_text = stem_text
            if parts_text:
                full_text += " " + " ".join(parts_text)

            all_qs.append({
                "id": qid,
                "paper": paper,
                "qnum": qnum,
                "marks": q.get("marks", 0) or 0,
                "full_text": full_text.strip(),
            })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(all_qs, f, ensure_ascii=False, indent=2)

    print(f"Collected {len(all_qs)} questions from {len(qp_files)} papers → {OUT}")
    return all_qs


if __name__ == "__main__":
    collect()
