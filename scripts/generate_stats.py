#!/usr/bin/env python3
"""Step 5: Generate tagging statistics."""

import json
import glob
from collections import Counter
from pathlib import Path

ROOT = Path("/Users/zhuxingzhe/Project/ExamBoard/25maths-edxwma12-json")


def main():
    syllabus = json.load(open(ROOT / "syllabus-wma12.json"))
    ch_map = {}
    sec_titles = {}
    for ch in syllabus["chapters"]:
        for s in ch["sections"]:
            ch_map[s["id"]] = ch["title"]
            sec_titles[s["id"]] = s["title"]

    qp_files = sorted(glob.glob(str(ROOT / "*/WMA*/*.json")))
    qp_files = [f for f in qp_files if not f.endswith("-ms.json") and not f.endswith(".raw") and "progress" not in f and "syllabus" not in f]

    section_counts = Counter()
    chapter_counts = Counter()
    cognitive = Counter()
    commands = Counter()
    section_marks = Counter()
    multi_topic = 0
    year_section = {}
    total = 0

    for f in qp_files:
        d = json.load(open(f))
        year = d.get("year", 0)
        for q in d.get("questions", []):
            total += 1
            meta = q.get("meta", {})
            sections = meta.get("sections", [])
            marks = q.get("marks", 0) or 0

            if len(sections) > 1:
                multi_topic += 1

            for s in sections:
                section_counts[s] += 1
                section_marks[s] += marks
                ch = ch_map.get(s, "?")
                chapter_counts[ch] += 1
                year_section.setdefault(year, Counter())[s] += 1

            cl = meta.get("cognitive_level", "")
            if cl:
                cognitive[cl] += 1

            for cw in meta.get("command_words", []):
                commands[cw] += 1

    # Print report
    print(f"{'=' * 60}")
    print(f"WMA12 Tagging Statistics")
    print(f"{'=' * 60}")
    print(f"  Total questions: {total}")
    print(f"  Multi-topic questions: {multi_topic} ({multi_topic * 100 // max(total, 1)}%)")

    print(f"\n📊 By Section:")
    for s in sorted(section_counts.keys()):
        c = section_counts[s]
        avg_marks = section_marks[s] / max(c, 1)
        title = sec_titles.get(s, s)
        pct = c * 100 // max(total, 1)
        bar = "█" * (c // 2)
        print(f"  {s:4s} {c:3d} ({pct:2d}%) avg {avg_marks:.1f}m  {title[:35]:35s} {bar}")

    print(f"\n📊 By Chapter:")
    for ch in sorted(set(chapter_counts.keys())):
        c = chapter_counts[ch]
        print(f"  {c:3d}  {ch}")

    print(f"\n📊 Cognitive Level:")
    for cl in ["AO1", "AO2", "AO3"]:
        c = cognitive.get(cl, 0)
        pct = c * 100 // max(total, 1)
        print(f"  {cl}: {c} ({pct}%)")

    print(f"\n📊 Top Command Words:")
    for cw, c in commands.most_common(10):
        print(f"  {c:3d}  {cw}")

    # Save
    stats = {
        "total_questions": total,
        "multi_topic_count": multi_topic,
        "section_counts": dict(section_counts),
        "chapter_counts": dict(chapter_counts),
        "cognitive_levels": dict(cognitive),
        "command_words": dict(commands.most_common(20)),
        "section_avg_marks": {s: round(section_marks[s] / max(section_counts[s], 1), 1) for s in section_counts},
    }
    with open(ROOT / "data" / "tagging_stats.json", "w") as f:
        json.dump(stats, f, indent=2)
    print(f"\n✅ Saved → {ROOT / 'data' / 'tagging_stats.json'}")


if __name__ == "__main__":
    main()
