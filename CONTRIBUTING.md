# Contributing

Thanks for helping improve this project.

## Good First Areas

- Improve the writing and evaluation UI
- Add tests around JSON loading, validation, and API routes
- Improve evaluator prompts and validation defaults
- Add more example essays in `examples/essays`
- Improve accessibility and responsive behavior
- Document setup issues for different AI CLI providers

## Local Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

Use `data/essays` for local test essays. Do not commit personal essay JSON files from `data/essays`.

## Data Conventions

Essay files are named:

```text
essay_<id>.json
```

Each essay should include:

- `id`
- `topic`
- `date`
- `type`
- `original_text`
- `status`
- `evaluation`
- `created_at`

When adding examples, keep them anonymous and suitable for public repositories.

## Pull Request Checklist

- The app starts with `python3 app.py`
- New runtime data is not committed from `data/essays`
- Example data belongs in `examples/essays`
- UI changes work on narrow and desktop widths
- Evaluation schema changes are reflected in `evaluate.py`, templates, and documentation
- README or docs are updated when setup or behavior changes
