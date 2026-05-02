// ── Word Counter ─────────────────────────────────
function updateWordCount() {
  const ta = document.getElementById('essay-text');
  const wc = document.getElementById('word-count');
  if (!ta || !wc) return;
  const words = ta.value.trim().split(/\s+/).filter(w => w.length > 0);
  wc.textContent = words.length + ' word' + (words.length !== 1 ? 's' : '');
}

// ── Autosave ─────────────────────────────────────
const DRAFT_KEY = 'essay_draft';

function saveDraft() {
  const form = document.getElementById('essay-form');
  if (!form || form.dataset.essayId) return; // don't autosave edits
  const draft = {
    topic: document.getElementById('topic').value,
    type: document.getElementById('essay-type').value,
    text: document.getElementById('essay-text').value,
    savedAt: Date.now()
  };
  localStorage.setItem(DRAFT_KEY, JSON.stringify(draft));
  const status = document.getElementById('autosave-status');
  if (status) {
    status.textContent = 'Draft saved';
    setTimeout(() => { status.textContent = ''; }, 2000);
  }
}

function loadDraft() {
  const form = document.getElementById('essay-form');
  if (!form || form.dataset.essayId) return;
  const raw = localStorage.getItem(DRAFT_KEY);
  if (!raw) return;
  try {
    const draft = JSON.parse(raw);
    // Only restore if less than 24 hours old
    if (Date.now() - draft.savedAt > 86400000) {
      localStorage.removeItem(DRAFT_KEY);
      return;
    }
    if (draft.text && draft.text.trim()) {
      const restore = confirm('You have an unsaved draft. Restore it?');
      if (restore) {
        document.getElementById('topic').value = draft.topic || '';
        setEssayType(draft.type || 'General');
        document.getElementById('essay-text').value = draft.text;
        updateWordCount();
      } else {
        localStorage.removeItem(DRAFT_KEY);
      }
    }
  } catch (e) {
    localStorage.removeItem(DRAFT_KEY);
  }
}

// ── Custom Select ─────────────────────────────────
function initCustomSelect() {
  const trigger = document.getElementById('type-trigger');
  const menu = document.getElementById('type-menu');
  const hiddenSelect = document.getElementById('essay-type');
  const label = document.getElementById('type-label');
  if (!trigger || !menu) return;

  trigger.addEventListener('click', (e) => {
    e.stopPropagation();
    const open = menu.classList.toggle('open');
    trigger.classList.toggle('open', open);
  });

  menu.querySelectorAll('.custom-option').forEach(opt => {
    opt.addEventListener('click', () => {
      setEssayType(opt.dataset.value);
      menu.classList.remove('open');
      trigger.classList.remove('open');
    });
  });

  document.addEventListener('click', () => {
    menu.classList.remove('open');
    trigger.classList.remove('open');
  });
}

function setEssayType(val) {
  const hiddenSelect = document.getElementById('essay-type');
  const label = document.getElementById('type-label');
  const menu = document.getElementById('type-menu');
  if (hiddenSelect) hiddenSelect.value = val;
  if (label) label.textContent = val;
  if (menu) {
    menu.querySelectorAll('.custom-option').forEach(opt => {
      opt.classList.toggle('selected', opt.dataset.value === val);
    });
  }
}

// ── Writing Timer ─────────────────────────────────
let timerSeconds = 0;
let timerInterval = null;
let timerRunning = false;
let timerStarted = false;

function formatTime(s) {
  return String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0');
}

function startTimer() {
  if (timerRunning) return;
  timerRunning = true;
  timerInterval = setInterval(() => {
    timerSeconds++;
    const d = document.getElementById('timer-display');
    if (d) d.textContent = formatTime(timerSeconds);
  }, 1000);
  const btn = document.getElementById('timer-toggle');
  if (btn) {
    btn.classList.remove('timer-paused');
    btn.title = 'Pause timer';
    btn.innerHTML = '<svg width="10" height="10" viewBox="0 0 10 10" fill="currentColor"><rect x="1.5" y="1" width="2.5" height="8" rx="1"/><rect x="6" y="1" width="2.5" height="8" rx="1"/></svg>';
  }
}

function pauseTimer() {
  if (!timerRunning) return;
  timerRunning = false;
  clearInterval(timerInterval);
  const btn = document.getElementById('timer-toggle');
  if (btn) {
    btn.classList.add('timer-paused');
    btn.title = 'Resume timer';
    btn.innerHTML = '<svg width="10" height="10" viewBox="0 0 10 10" fill="currentColor"><path d="M2 1.5l7 3.5-7 3.5z"/></svg>';
  }
}

// ── Write Page Init ──────────────────────────────
function initWritePage() {
  const ta = document.getElementById('essay-text');
  if (!ta) return;

  initCustomSelect();

  ta.addEventListener('input', () => {
    updateWordCount();
    if (!timerStarted && ta.value.trim()) {
      timerStarted = true;
      const widget = document.getElementById('writing-timer');
      if (widget) widget.classList.add('active');
      startTimer();
    }
  });

  const toggleBtn = document.getElementById('timer-toggle');
  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      if (timerRunning) pauseTimer(); else startTimer();
    });
  }

  updateWordCount();

  loadDraft();

  // Autosave every 30 seconds
  setInterval(saveDraft, 30000);

  // Form submit
  const form = document.getElementById('essay-form');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = document.getElementById('essay-text').value.trim();
    if (!text) {
      alert('Please write your essay before saving.');
      return;
    }

    const words = text.split(/\s+/).filter(w => w.length > 0);
    if (words.length < 50) {
      const ok = confirm(`Your essay is only ${words.length} words. Are you sure you want to save?`);
      if (!ok) return;
    }

    const payload = {
      topic: document.getElementById('topic').value.trim(),
      type: document.getElementById('essay-type').value,
      original_text: text
    };

    const btn = document.getElementById('save-btn');
    btn.disabled = true;
    btn.textContent = 'Saving...';

    try {
      const essayId = form.dataset.essayId;
      let res;
      if (essayId) {
        res = await fetch(`/api/essays/${essayId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (res.ok) {
          localStorage.removeItem(DRAFT_KEY);
          window.location.href = `/essay/${essayId}`;
        }
      } else {
        res = await fetch('/api/essays', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (res.ok) {
          const data = await res.json();
          localStorage.removeItem(DRAFT_KEY);
          window.location.href = `/essay/${data.id}`;
        }
      }
      if (!res.ok) {
        const err = await res.json();
        alert(err.error || 'Failed to save');
      }
    } catch (err) {
      alert('Network error. Please try again.');
    } finally {
      btn.disabled = false;
      btn.textContent = 'Save Essay';
    }
  });
}

// ── Evaluate ─────────────────────────────────────
async function requestEvaluation(essayId) {
  const btn = document.getElementById('evaluate-btn');
  if (btn) {
    btn.disabled = true;
    btn.textContent = 'Starting...';
  }

  try {
    const res = await fetch(`/api/essays/${essayId}/evaluate`, { method: 'POST' });
    if (res.ok) {
      window.location.reload();
    } else {
      const data = await res.json();
      alert(data.error || 'Failed to start evaluation');
      if (btn) {
        btn.disabled = false;
        btn.textContent = 'Evaluate with Codex';
      }
    }
  } catch (err) {
    alert('Network error');
    if (btn) {
      btn.disabled = false;
      btn.textContent = 'Evaluate with Codex';
    }
  }
}

// ── Poll Status ──────────────────────────────────
function pollStatus(essayId) {
  const interval = setInterval(async () => {
    try {
      const res = await fetch(`/api/essays/${essayId}/status`);
      const data = await res.json();
      if (data.status !== 'evaluating') {
        clearInterval(interval);
        window.location.reload();
      }
    } catch (e) {
      // ignore network errors, keep polling
    }
  }, 3000);
}

// ── Delete ───────────────────────────────────────
async function deleteEssay(essayId) {
  if (!confirm('Are you sure you want to delete this essay?')) return;
  try {
    await fetch(`/api/essays/${essayId}`, { method: 'DELETE' });
    window.location.href = '/';
  } catch (e) {
    alert('Failed to delete');
  }
}

// ── Tab Switching ────────────────────────────────
function switchTab(btn, tabId) {
  const section = btn.closest('.section-block');
  section.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  section.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById(tabId).classList.add('active');
}

// ── Copy CLI command ─────────────────────────────
function copyCmd() {
  const code = document.getElementById('cli-cmd');
  if (!code) return;
  navigator.clipboard.writeText(code.textContent).then(() => {
    const btn = code.nextElementSibling;
    btn.textContent = 'Copied!';
    setTimeout(() => { btn.textContent = 'Copy'; }, 1500);
  });
}
