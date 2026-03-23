#!/usr/bin/env python3
"""Step 2: Tag WMA12 questions using Gemini batch classification."""

import json
import re
import sys
import time
from pathlib import Path

ROOT = Path("/Users/zhuxingzhe/Project/ExamBoard/25maths-edxwma12-json")
INPUT = ROOT / "data" / "all_questions.json"
OUTPUT = ROOT / "data" / "tagged_results.json"
BATCH_SIZE = 50

PROMPT_TEMPLATE = """\
You are an Edexcel IAL Pure Mathematics 2 (WMA12) exam specialist.
Classify each question below into WMA12 syllabus sections.

## Syllabus Sections

| ID  | Title | Key Content |
|-----|-------|-------------|
| 1.1 | Structure of mathematical proof | logical steps, deduction, algebraic proof |
| 1.2 | Proof by exhaustion | trying all cases |
| 1.3 | Disproof by counter-example | showing a statement is untrue |
| 2.1 | Algebraic division, factor and remainder theorems | polynomial division, f(a)=0, factorise cubics |
| 3.1 | Equation of a circle | (x-a)^2+(y-b)^2=r^2, tangent, chord, semicircle properties |
| 4.1 | Sequences and recurrence relations | x_{n+1}=f(x_n), nth term formula |
| 4.2 | Arithmetic sequences and series | common difference, sum formula, sigma notation |
| 4.3 | Increasing, decreasing and periodic sequences | convergent, divergent, periodic |
| 4.4 | Geometric sequences and series | common ratio, sum to infinity, |r|<1 |
| 4.5 | Binomial expansion | (a+bx)^n for positive integer n, Pascal's triangle, nCr |
| 5.1 | Exponential functions | y=a^x and its graph |
| 5.2 | Laws of logarithms | log rules, simplification, change of base |
| 5.3 | Solving exponential equations | a^x=b, using logs to solve |
| 6.1 | Trigonometric identities | tan=sin/cos, sin^2+cos^2=1 |
| 6.2 | Solving trigonometric equations | in given intervals, quadratic trig |
| 7.1 | Maxima, minima and stationary points | dy/dx=0, increasing/decreasing, second derivative test |
| 8.1 | Definite integrals | evaluation of definite integrals |
| 8.2 | Area under a curve | bounded regions, area between curves and lines |
| 8.3 | The trapezium rule | numerical approximation with strips |

## Disambiguation Rules

1. Differentiation to find stationary points → 7.1 (even if other topics appear)
2. Evaluating a definite integral without area context → 8.1; asking for area/region → 8.2
3. Logs used to SOLVE a^x=b → 5.3; logs simplified/manipulated → 5.2
4. Sequence with sigma notation for sum → 4.2 or 4.4 (not 4.1)
5. "Prove"/"show that" about a specific topic → primary is that topic, secondary 1.1
6. Trig identities used to SOLVE an equation → primary 6.2, secondary 6.1
7. Circle + differentiation for tangent → primary 3.1, secondary 7.1
8. Binomial expansion + integration → list both (4.5 and 8.1/8.2)

## Output

Return ONLY valid JSON (no markdown fences):
{"results": [
  {"id": "...", "sections": ["4.5"], "primary_section": "4.5", "question_type": "binomial expansion", "command_words": ["Find"], "cognitive_level": "AO1"},
  ...
]}

Rules:
- 1-3 sections per question, ordered by importance
- primary_section = main topic assessed
- question_type = concise description (5-10 words)
- command_words = extract from question text (Find, Show that, Prove, Solve, Sketch, etc.)
- cognitive_level: AO1 (routine procedure), AO2 (reasoning/proof), AO3 (problem-solving/modelling)

## Questions

"""


def tag_batch(questions: list) -> list:
    import google.generativeai as genai

    batch_text = ""
    for q in questions:
        batch_text += f"--- {q['id']} ({q['marks']} marks) ---\n{q['full_text']}\n\n"

    prompt = PROMPT_TEMPLATE + batch_text

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)

    raw = response.text
    raw = re.sub(r"^```(?:json)?\s*\n?", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"\n?```\s*$", "", raw, flags=re.MULTILINE)
    raw = raw.strip()

    # Parse JSON
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        print(f"  ERROR: No JSON found", file=sys.stderr)
        return []

    json_str = raw[start:end + 1]
    for _ in range(50):
        try:
            data = json.loads(json_str)
            break
        except json.JSONDecodeError as e:
            if "Invalid \\escape" in str(e) and e.pos > 0:
                json_str = json_str[:e.pos - 1] + "\\\\" + json_str[e.pos:]
            else:
                print(f"  ERROR: {e}", file=sys.stderr)
                return []

    return data.get("results", [])


def main():
    questions = json.load(open(INPUT))
    print(f"Loaded {len(questions)} questions")

    all_results = []
    total_batches = (len(questions) + BATCH_SIZE - 1) // BATCH_SIZE

    for i in range(total_batches):
        start = i * BATCH_SIZE
        end = min(start + BATCH_SIZE, len(questions))
        batch = questions[start:end]

        print(f"[{i + 1}/{total_batches}] Tagging {len(batch)} questions ({batch[0]['id']} → {batch[-1]['id']})...")

        results = tag_batch(batch)
        all_results.extend(results)
        print(f"  ✅ Got {len(results)} results")

        if i < total_batches - 1:
            time.sleep(3)

    # Save
    with open(OUTPUT, "w") as f:
        json.dump({"results": all_results}, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Tagged {len(all_results)}/{len(questions)} questions → {OUTPUT}")

    # Quick stats
    from collections import Counter
    sections = Counter()
    for r in all_results:
        for s in r.get("sections", []):
            sections[s] += 1
    print("\nSection distribution:")
    for s, c in sorted(sections.items()):
        print(f"  {s}: {c}")


if __name__ == "__main__":
    main()
