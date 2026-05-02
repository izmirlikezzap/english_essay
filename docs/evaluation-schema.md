# Evaluation Schema

`evaluate.py` asks the selected AI provider to return one JSON object. The validator accepts missing optional sections and fills safe defaults.

Required top-level fields:

- `spelling_mistakes`
- `grammar_mistakes`
- `corrected_version`
- `scores`
- `notes`

Required score fields:

- `vocabulary`
- `grammar`
- `coherence`

Optional sections used by the UI:

- `structure`
- `suggested_phrases`
- `vocabulary_suggestions`
- `linking_words`
- `resolved_mistakes`
- `still_recurring`

If you change this schema, update these files together:

- `evaluate.py`
- `templates/view.html`
- `static/style.css`
- `README.md`
