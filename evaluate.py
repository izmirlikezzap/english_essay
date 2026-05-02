#!/usr/bin/env python3
"""
Evaluate an essay using an AI CLI.

Usage:
  python3 evaluate.py data/essays/essay_3.json
"""

import json
import os
import sys
import subprocess
import re
import tempfile
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ESSAYS_DIR = os.environ.get('ESSAYS_DIR', os.path.join(BASE_DIR, 'data', 'essays'))
DEFAULT_PROVIDER = os.environ.get('EVALUATION_PROVIDER', 'codex').strip().lower() or 'codex'
DEFAULT_CODEX_MODEL = os.environ.get('CODEX_MODEL', 'gpt-5').strip() or 'gpt-5'
DEFAULT_CLAUDE_MODEL = os.environ.get('CLAUDE_MODEL', '').strip()


def load_previous_mistakes(current_id):
    """Load grammar/spelling mistakes from all previously evaluated essays."""
    mistakes = []
    for fname in sorted(os.listdir(ESSAYS_DIR)):
        if not fname.startswith('essay_') or not fname.endswith('.json'):
            continue
        try:
            eid = int(fname.replace('essay_', '').replace('.json', ''))
        except ValueError:
            continue
        if eid >= current_id:
            continue
        filepath = os.path.join(ESSAYS_DIR, fname)
        with open(filepath, 'r', encoding='utf-8') as f:
            essay = json.load(f)
        ev = essay.get('evaluation')
        if not ev or essay.get('status') != 'evaluated':
            continue
        for m in ev.get('spelling_mistakes', []):
            mistakes.append(f"Essay #{eid}: {m.get('wrong')} → {m.get('correct')}")
        for m in ev.get('grammar_mistakes', []):
            mistakes.append(f"Essay #{eid}: {m.get('wrong')} → {m.get('correct')}")
    return mistakes


def build_prompt(essay, previous_mistakes):
    prev_section = ""
    if previous_mistakes:
        prev_list = "\n".join(f"- {m}" for m in previous_mistakes[-30:])
        prev_section = f"""

The student has made these mistakes in previous essays. Check if any are repeated:
{prev_list}
"""

    return f"""You are an English writing tutor evaluating an essay written by a Turkish student learning English.

Topic: {essay.get('topic', 'General')}
Essay Type: {essay.get('type', 'General')}

Student's Essay:
---
{essay['original_text']}
---
{prev_section}
Evaluate this essay and return ONLY a valid JSON object with this exact structure (no markdown fences, no extra text):
{{
  "spelling_mistakes": [{{"wrong": "misspelled word", "correct": "correct spelling"}}],
  "grammar_mistakes": [{{"wrong": "original phrase with context", "correct": "corrected phrase"}}],
  "corrected_version": "the full corrected essay preserving the student's voice and ideas",
  "scores": {{"vocabulary": 7, "grammar": 6, "coherence": 7}},
  "notes": ["practical tip 1", "practical tip 2"],
  "structure": {{
    "paragraphs": [
      {{"type": "introduction", "feedback": "analysis of the introduction paragraph"}},
      {{"type": "body", "feedback": "analysis of each body paragraph"}},
      {{"type": "conclusion", "feedback": "analysis of the conclusion"}}
    ],
    "overall": "overall structure feedback"
  }},
  "suggested_phrases": {{
    "introduction": ["phrase 1 suitable for this essay type", "phrase 2"],
    "body": ["transition/argument phrase 1", "phrase 2"],
    "conclusion": ["concluding phrase 1", "phrase 2"]
  }},
  "vocabulary_suggestions": [
    {{"used": "simple word the student used", "alternatives": ["stronger synonym 1", "synonym 2", "synonym 3"]}}
  ],
  "linking_words": {{
    "used": ["linking words the student actually used"],
    "missing_types": ["types of transitions not used, e.g. cause/effect, contrast"],
    "suggestions": ["suggested linking words they should try using"]
  }},
  "resolved_mistakes": [
    {{"pattern": "name of the mistake type that was fixed", "example": "what the student used to get wrong and now does correctly"}}
  ],
  "still_recurring": [
    {{"pattern": "type of mistake still being repeated", "count": 2, "essays": [1, 3], "example": "specific example from this and previous essays"}}
  ]
}}

Rules:
- Scores are integers from 1 to 10
- For grammar mistakes, include enough surrounding words so the student can locate the error
- The corrected version should keep the student's original ideas and structure
- Notes should be 3-5 actionable tips for improvement
- Structure: label each paragraph as introduction, body, or conclusion. Give specific feedback for each.
- Suggested phrases: provide 3-5 phrases per section (intro/body/conclusion) that fit the essay type ({essay.get('type', 'General')}). These should be phrases the student can memorize and reuse.
- Vocabulary suggestions: find 3-8 simple/repeated words and suggest stronger alternatives
- Linking words: list what the student used, identify missing transition types, and suggest specific alternatives
- resolved_mistakes: mistakes from previous essays that the student has NOW fixed in this essay. These are POSITIVE — the student learned from past corrections. If no previous essays or no resolved patterns, return empty array.
- still_recurring: mistakes that appear BOTH in previous essays AND in this current essay. The student keeps making these despite corrections. Include which essay numbers had this mistake. If no previous essays or no recurring patterns, return empty array.
- Return ONLY valid JSON, nothing else"""


def extract_json(text):
    """Extract JSON from an AI response, handling markdown fences."""
    fence_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1)

    brace_start = text.find('{')
    if brace_start == -1:
        raise ValueError("No JSON object found in response")

    depth = 0
    for i in range(brace_start, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return json.loads(text[brace_start:i + 1])

    raise ValueError("Incomplete JSON object")


def validate_evaluation(ev):
    """Ensure the evaluation has all required fields."""
    required = ['spelling_mistakes', 'grammar_mistakes', 'corrected_version', 'scores', 'notes']
    for key in required:
        if key not in ev:
            raise ValueError(f"Missing field: {key}")

    scores = ev['scores']
    for key in ['vocabulary', 'grammar', 'coherence']:
        if key not in scores:
            raise ValueError(f"Missing score: {key}")
        val = scores[key]
        if not isinstance(val, (int, float)) or val < 1 or val > 10:
            scores[key] = max(1, min(10, int(val)))

    for key in ['spelling_mistakes', 'grammar_mistakes', 'notes']:
        if not isinstance(ev.get(key), list):
            ev[key] = []

    # Validate new fields with safe defaults
    if not isinstance(ev.get('structure'), dict):
        ev['structure'] = {'paragraphs': [], 'overall': ''}
    else:
        if not isinstance(ev['structure'].get('paragraphs'), list):
            ev['structure']['paragraphs'] = []
        if not isinstance(ev['structure'].get('overall'), str):
            ev['structure']['overall'] = ''

    if not isinstance(ev.get('suggested_phrases'), dict):
        ev['suggested_phrases'] = {'introduction': [], 'body': [], 'conclusion': []}
    else:
        for key in ['introduction', 'body', 'conclusion']:
            if not isinstance(ev['suggested_phrases'].get(key), list):
                ev['suggested_phrases'][key] = []

    if not isinstance(ev.get('vocabulary_suggestions'), list):
        ev['vocabulary_suggestions'] = []

    if not isinstance(ev.get('linking_words'), dict):
        ev['linking_words'] = {'used': [], 'missing_types': [], 'suggestions': []}
    else:
        for key in ['used', 'missing_types', 'suggestions']:
            if not isinstance(ev['linking_words'].get(key), list):
                ev['linking_words'][key] = []

    if not isinstance(ev.get('resolved_mistakes'), list):
        ev['resolved_mistakes'] = []

    if not isinstance(ev.get('still_recurring'), list):
        ev['still_recurring'] = []

    # Migrate old format if present
    ev.pop('recurring_mistakes', None)

    return ev


def run_codex(prompt):
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', delete=False) as tmp:
        output_path = tmp.name

    try:
        command = [
            'codex',
            'exec',
            '--skip-git-repo-check',
            '--color',
            'never',
            '--model',
            DEFAULT_CODEX_MODEL,
            '-C',
            BASE_DIR,
            '-o',
            output_path,
            prompt,
        ]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=BASE_DIR,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Codex CLI error: {result.stderr or result.stdout}")

        with open(output_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)


def run_claude(prompt):
    command = ['claude', '-p', prompt, '--output-format', 'json']
    if DEFAULT_CLAUDE_MODEL:
        command.extend(['--model', DEFAULT_CLAUDE_MODEL])

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=180
    )

    if result.returncode != 0:
        raise RuntimeError(f"Claude CLI error: {result.stderr or result.stdout}")

    response = json.loads(result.stdout)
    return response.get('result', result.stdout)


def run_evaluator(prompt):
    provider = DEFAULT_PROVIDER
    if provider == 'claude':
        return run_claude(prompt)
    if provider == 'codex':
        return run_codex(prompt)
    raise ValueError(f"Unsupported EVALUATION_PROVIDER: {provider}")


def evaluate(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        essay = json.load(f)

    if not essay.get('original_text', '').strip():
        essay['status'] = 'error'
        essay['error_message'] = 'Essay text is empty'
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(essay, f, ensure_ascii=False, indent=2)
        return

    essay['status'] = 'evaluating'
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(essay, f, ensure_ascii=False, indent=2)

    previous_mistakes = load_previous_mistakes(essay.get('id', 999))
    prompt = build_prompt(essay, previous_mistakes)

    max_attempts = 2
    last_error = None

    for attempt in range(max_attempts):
        try:
            response_text = run_evaluator(prompt)
            evaluation = extract_json(response_text)
            evaluation = validate_evaluation(evaluation)
            evaluation['evaluated_at'] = datetime.now().isoformat()

            essay['evaluation'] = evaluation
            essay['status'] = 'evaluated'
            essay.pop('error_message', None)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(essay, f, ensure_ascii=False, indent=2)

            print(f"Evaluation complete: {filepath}")
            return

        except Exception as e:
            last_error = str(e)
            print(f"Attempt {attempt + 1} failed: {last_error}")

    # All attempts failed
    essay['status'] = 'error'
    essay['error_message'] = f"Evaluation failed: {last_error}"
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(essay, f, ensure_ascii=False, indent=2)
    print(f"Evaluation failed: {filepath}")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python3 evaluate.py data/essays/essay_X.json")
        sys.exit(1)
    evaluate(sys.argv[1])
