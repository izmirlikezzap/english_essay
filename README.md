# English Writing Practice

A small Flask app for writing English essays and getting structured feedback from an AI CLI evaluator.

The app stores essays as JSON files, lets users edit or delete them, and can evaluate each essay for spelling, grammar, structure, vocabulary, linking words, and recurring mistakes.

## Features

- Write and edit essays from the browser
- Save essays as local JSON files
- Evaluate essays with Codex or Claude CLI
- Track scores for vocabulary, grammar, and coherence
- See corrected versions, suggested phrases, and recurring mistake patterns
- Keep runtime data separate from example data

## Project Structure

```text
.
├── app.py                  # Flask web app and API routes
├── evaluate.py             # AI evaluation runner
├── data/essays/            # Local runtime essay JSON files, ignored by git
├── examples/essays/        # Example essay JSON files for contributors
├── static/                 # Frontend JavaScript and CSS
├── templates/              # Jinja templates
├── docs/                   # Extra project notes
├── requirements.txt
└── .env.example
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optional environment setup:

```bash
cp .env.example .env
```

The app works without a `.env` file. By default, new essays are stored in `data/essays`.

## Run

```bash
python3 app.py
```

Open `http://localhost:5050`.

## Evaluate an Essay

From the app, open a saved essay and click **Evaluate with Codex**.

You can also run evaluation manually:

```bash
python3 evaluate.py data/essays/essay_1.json
```

By default, the evaluator uses Codex:

```bash
EVALUATION_PROVIDER=codex CODEX_MODEL=gpt-5 python3 evaluate.py data/essays/essay_1.json
```

To use Claude:

```bash
EVALUATION_PROVIDER=claude python3 evaluate.py data/essays/essay_1.json
```

## Example Data

Example essays live in `examples/essays`. They are committed so contributors can understand the JSON shape and expected evaluation output.

Runtime essays live in `data/essays` and are ignored by git to avoid committing personal writing by accident.

To try the app with an example file:

```bash
cp examples/essays/essay_1.json data/essays/
python3 app.py
```
