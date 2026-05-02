import json
import os
import subprocess
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ESSAYS_DIR = os.environ.get('ESSAYS_DIR', os.path.join(BASE_DIR, 'data', 'essays'))
os.makedirs(ESSAYS_DIR, exist_ok=True)


# ── JSON helpers ──────────────────────────────────────────────

def get_essay_path(essay_id):
    return os.path.join(ESSAYS_DIR, f'essay_{essay_id}.json')


def get_display_path(path):
    try:
        return os.path.relpath(path, BASE_DIR)
    except ValueError:
        return path


def read_essay(essay_id):
    path = get_essay_path(essay_id)
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_essay(data):
    path = get_essay_path(data['id'])
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def list_essays():
    essays = []
    for fname in os.listdir(ESSAYS_DIR):
        if fname.startswith('essay_') and fname.endswith('.json'):
            with open(os.path.join(ESSAYS_DIR, fname), 'r', encoding='utf-8') as f:
                essays.append(json.load(f))
    essays.sort(key=lambda e: e['id'], reverse=True)
    return essays


def next_id():
    existing = []
    for fname in os.listdir(ESSAYS_DIR):
        if fname.startswith('essay_') and fname.endswith('.json'):
            try:
                existing.append(int(fname.replace('essay_', '').replace('.json', '')))
            except ValueError:
                pass
    return max(existing, default=0) + 1


# ── Routes ────────────────────────────────────────────────────

@app.route('/')
def index():
    essays = list_essays()
    return render_template('index.html', essays=essays)


@app.route('/write')
def write_page():
    return render_template('write.html')


@app.route('/essay/<int:essay_id>')
def view_essay(essay_id):
    essay = read_essay(essay_id)
    if not essay:
        return redirect(url_for('index'))
    return render_template(
        'view.html',
        essay=essay,
        essay_file_path=get_display_path(get_essay_path(essay_id)),
    )


@app.route('/essay/<int:essay_id>/edit')
def edit_essay(essay_id):
    essay = read_essay(essay_id)
    if not essay:
        return redirect(url_for('index'))
    return render_template('write.html', essay=essay)


# ── API ───────────────────────────────────────────────────────

@app.route('/api/essays', methods=['POST'])
def create_essay():
    data = request.get_json()
    topic = (data.get('topic') or '').strip()
    original_text = (data.get('original_text') or '').strip()
    essay_type = (data.get('type') or 'General').strip()

    if not original_text:
        return jsonify({'error': 'Essay text cannot be empty'}), 400

    essay = {
        'id': next_id(),
        'topic': topic or 'Untitled',
        'date': datetime.now().strftime('%Y-%m-%d'),
        'type': essay_type,
        'original_text': original_text,
        'status': 'pending',
        'evaluation': None,
        'created_at': datetime.now().isoformat()
    }
    write_essay(essay)
    return jsonify({'id': essay['id']}), 201


@app.route('/api/essays/<int:essay_id>', methods=['PUT'])
def update_essay(essay_id):
    essay = read_essay(essay_id)
    if not essay:
        return jsonify({'error': 'Not found'}), 404

    data = request.get_json()
    if 'topic' in data:
        essay['topic'] = data['topic'].strip() or 'Untitled'
    if 'original_text' in data:
        text = data['original_text'].strip()
        if not text:
            return jsonify({'error': 'Essay text cannot be empty'}), 400
        essay['original_text'] = text
        essay['status'] = 'pending'
        essay['evaluation'] = None
    if 'type' in data:
        essay['type'] = data['type'].strip() or 'General'

    write_essay(essay)
    return jsonify({'ok': True})


@app.route('/api/essays/<int:essay_id>', methods=['DELETE'])
def delete_essay(essay_id):
    path = get_essay_path(essay_id)
    if os.path.exists(path):
        os.remove(path)
    return jsonify({'ok': True})


@app.route('/api/essays/<int:essay_id>/evaluate', methods=['POST'])
def evaluate_essay(essay_id):
    essay = read_essay(essay_id)
    if not essay:
        return jsonify({'error': 'Not found'}), 404
    if essay['status'] == 'evaluating':
        return jsonify({'error': 'Already evaluating'}), 409

    essay['status'] = 'evaluating'
    write_essay(essay)

    script = os.path.join(BASE_DIR, 'evaluate.py')
    filepath = get_essay_path(essay_id)
    subprocess.Popen([sys.executable, script, filepath])

    return jsonify({'ok': True, 'status': 'evaluating'})


@app.route('/api/essays/<int:essay_id>/status')
def essay_status(essay_id):
    essay = read_essay(essay_id)
    if not essay:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({'status': essay['status']})


if __name__ == '__main__':
    print('\n  English Writing Practice')
    print('  http://localhost:5050\n')
    app.run(debug=True, port=5050)
