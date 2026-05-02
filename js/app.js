/* ============================================================
   HorseTrainer.ai — Core Application JS
   Intake Form · AI Assistant · Risk Rules · Trainer Matcher · UI
   ============================================================ */

'use strict';

// ── CONFIG ───────────────────────────────────────────────────
const CONFIG = {
  // Replace with your deployed Cloudflare Worker URL
  WORKER_URL: 'https://horse-trainer-proxy.bridleandbit.workers.dev',
  SUPABASE_URL: 'https://ptuuuishzwwgmaexneul.supabase.co',
  SUPABASE_ANON: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB0dXV1aXNoend3Z21hZXhuZXVsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc2ODQ4NTAsImV4cCI6MjA5MzI2MDg1MH0.y55GTkYHdfzh1P9Gv4AFoox7ahC_Y9Pr4gqsyF-da3c',
};

// ── INTAKE STATE ─────────────────────────────────────────────
const intakeState = {
  currentStep: 1,
  totalSteps: 7,
  data: {
    discipline: null,
    horse_age: null,
    training_situation: null,
    problems: [],
    danger_rating: 2,
    rider_level: null,
    state: null,
    zip: null,
    travel_radius: '50',
    budget: null,
    online_ok: false,
  },
};

// ── RISK RULES ───────────────────────────────────────────────
const RISK_RULES = {
  evaluate(data) {
    const { problems = [], danger_rating = 1, rider_level } = data;
    let level = 'green';
    let messages = [];
    let trainerRequired = false;
    let pain_flag = false;

    // Red triggers
    if (problems.includes('rearing')) {
      level = 'red';
      trainerRequired = true;
      messages.push('Rearing is one of the most dangerous behaviors in horses. This requires a professional problem horse specialist. Do not attempt alone.');
    }
    if (problems.includes('bolting') && ['beginner','complete_beginner'].includes(rider_level)) {
      level = 'red';
      trainerRequired = true;
      messages.push('A bolting horse combined with a beginner rider is a serious safety risk. Please work with a professional.');
    }
    if (danger_rating >= 4) {
      level = 'red';
      trainerRequired = true;
      messages.push('With a danger rating of ' + danger_rating + '/5, this situation requires a professional trainer immediately.');
    }

    // Yellow triggers
    if (level !== 'red') {
      if (problems.includes('bucking') && danger_rating >= 3) { level = 'yellow'; messages.push('Bucking at this intensity warrants a professional evaluation before proceeding.'); }
      if (problems.includes('bolting')) { level = 'yellow'; messages.push('A bolting horse requires systematic desensitization. Consider professional guidance.'); }
      if (danger_rating === 3) { level = 'yellow'; messages.push('This situation warrants a professional trainer consultation.'); }
    }

    // Pain flag
    if (problems.some(p => ['head_tossing','cinchy','bucking','resistance'].includes(p))) {
      pain_flag = true;
    }

    return { level, messages, trainerRequired, pain_flag };
  }
};

// ── TRAINER CATEGORY MAPPING ─────────────────────────────────
const TRAINER_CATEGORIES = {
  reining:          { label: 'Reining Trainer',             url: '/find-a-trainer/reining-trainers/' },
  cutting:          { label: 'Cutting Trainer',             url: '/find-a-trainer/cutting-trainers/' },
  barrel_racing:    { label: 'Barrel Racing Trainer',       url: '/find-a-trainer/barrel-racing-trainers/' },
  colt_starting:    { label: 'Colt Starter',                url: '/find-a-trainer/colt-starters/' },
  problem_horse:    { label: 'Problem Horse Specialist',    url: '/find-a-trainer/problem-horse-specialists/' },
  dressage:         { label: 'Dressage Trainer',            url: '/find-a-trainer/dressage-trainers/' },
  hunter_jumper:    { label: 'Hunter/Jumper Trainer',       url: '/find-a-trainer/hunter-jumper-trainers/' },
  trail:            { label: 'Trail/Desensitizing Trainer', url: '/find-a-trainer/trail-trainers/' },
  mustang:          { label: 'Mustang Trainer',             url: '/find-a-trainer/mustang-trainers/' },
  ranch:            { label: 'Ranch Horse Trainer',         url: '/find-a-trainer/ranch-trainers/' },
  groundwork:       { label: 'Groundwork Specialist',       url: '/find-a-trainer/groundwork-trainers/' },
  working_cow:      { label: 'Working Cow Horse Trainer',   url: '/find-a-trainer/cow-horse-trainers/' },
  youth:            { label: 'Youth / Amateur Coach',       url: '/find-a-trainer/youth-coaches/' },
  online:           { label: 'Online Coaching',             url: '/find-a-trainer/online-trainers/' },
  rehab:            { label: 'Rehab / Restart Trainer',     url: '/find-a-trainer/rehab-trainers/' },
};

function getTrainerCategory(data) {
  const { problems = [], training_situation, discipline, rider_level } = data;

  // Problem horse overrides
  if (problems.some(p => ['rearing','bolting','bucking'].includes(p))) return TRAINER_CATEGORIES.problem_horse;
  if (problems.length > 1) return TRAINER_CATEGORIES.problem_horse;

  // Situation-based
  if (training_situation === 'starting_young') {
    if (discipline === 'mustang') return TRAINER_CATEGORIES.mustang;
    return TRAINER_CATEGORIES.colt_starting;
  }
  if (training_situation === 'rehab') return TRAINER_CATEGORIES.rehab;
  if (training_situation === 'trail_safe') return TRAINER_CATEGORIES.trail;
  if (['beginner','complete_beginner'].includes(rider_level) && !problems.length) return TRAINER_CATEGORIES.youth;

  // Discipline-based
  return TRAINER_CATEGORIES[discipline] || TRAINER_CATEGORIES.groundwork;
}

// ── RELATED PAGES MAPPING ─────────────────────────────────────
const RELATED_PAGES = {
  rearing:       [{ title: 'Understanding Why Horses Rear', url: '/problem-horse/rearing/' }, { title: 'Problem Horse Specialists', url: '/find-a-trainer/problem-horse-specialists/' }],
  bucking:       [{ title: 'Why Horses Buck — Causes & Fixes', url: '/problem-horse/bucking/' }, { title: 'Saddle Fit Guide', url: '/tack/saddle-fit-guide/' }],
  bolting:       [{ title: 'No-Whoa / Runaway Horse', url: '/problem-horse/no-whoa-runaway-horse/' }, { title: 'Building the Stop', url: '/colt-starting/developing-the-stop/' }],
  barn_sour:     [{ title: 'Barn Sour / Buddy Sour Horse', url: '/problem-horse/barn-sour-horse/' }, { title: 'Desensitizing for Trail', url: '/trail/desensitizing-for-trail/' }],
  wont_load:     [{ title: 'Trailer Loading Step by Step', url: '/groundwork/trailer-loading-step-by-step/' }],
  cinchy:        [{ title: 'Cinchy / Girthy Horse', url: '/problem-horse/cinchy-girthy-horse/' }, { title: 'Saddle Fit Guide', url: '/tack/saddle-fit-guide/' }],
  head_tossing:  [{ title: 'Head Tossing Causes & Fixes', url: '/problem-horse/head-tossing-causes-and-fixes/' }, { title: 'Bit Selection Guide', url: '/tack/bit-selection-western/' }],
  spooky:        [{ title: 'Desensitizing to Tarps & Bags', url: '/groundwork/desensitizing-to-tarps-and-bags/' }, { title: 'Building a Bombproof Trail Horse', url: '/trail/building-a-bombproof-trail-horse/' }],
  reining:       [{ title: 'Introduction to Reining', url: '/reining/' }, { title: 'Teaching the Sliding Stop', url: '/reining/teaching-the-sliding-stop/' }, { title: 'Developing Lead Changes', url: '/reining/developing-lead-changes/' }],
  barrel_racing: [{ title: 'Introduction to Barrel Racing', url: '/barrel-racing/' }, { title: 'Pattern Fundamentals', url: '/barrel-racing/pattern-fundamentals/' }],
  dressage:      [{ title: 'Introduction to Dressage', url: '/dressage/' }, { title: 'The Training Scale Explained', url: '/dressage/training-scale-explained/' }],
  colt_starting: [{ title: 'First 60 Days Under Saddle', url: '/colt-starting/first-60-days-under-saddle/' }, { title: 'Colt Starting Groundwork', url: '/groundwork/first-saddling-colt-starting/' }],
  groundwork:    [{ title: 'Round Pen Fundamentals', url: '/groundwork/round-pen-fundamentals/' }, { title: 'Yielding Hindquarters', url: '/groundwork/yielding-hindquarters/' }, { title: 'Groundwork Overview', url: '/groundwork/' }],
  trail:         [{ title: 'Building a Bombproof Trail Horse', url: '/trail/building-a-bombproof-trail-horse/' }, { title: 'Trail Obstacles Training', url: '/trail/trail-obstacles-training/' }],
  mustang:       [{ title: 'First 30 Days with a Mustang', url: '/mustang/first-30-days-with-a-mustang/' }, { title: 'Mustang Halter Training', url: '/mustang/mustang-halter-training/' }],
};

function getRelatedPages(data) {
  const { problems = [], discipline } = data;
  let pages = [];
  for (const p of problems) {
    if (RELATED_PAGES[p]) pages.push(...RELATED_PAGES[p]);
    if (pages.length >= 3) break;
  }
  if (pages.length < 2 && discipline && RELATED_PAGES[discipline]) {
    pages.push(...RELATED_PAGES[discipline]);
  }
  // Dedupe by URL
  const seen = new Set();
  return pages.filter(p => { if (seen.has(p.url)) return false; seen.add(p.url); return true; }).slice(0, 3);
}

// ── AI PATHWAY GENERATOR (client-side fallback / Worker augment) ──
function generateLocalPathway(data) {
  const { problems = [], discipline, training_situation, rider_level, horse_age } = data;

  const pathways = {
    rearing: null, // RED — never show steps
    bucking: ['Rule out pain first — have your vet check back, teeth, and saddle fit.', 'Work horse on the ground until the cause is identified.', 'Consult a problem horse specialist before getting back in the saddle.'],
    bolting: ['Build a solid emergency one-rein stop on the ground first.', 'Practice the one-rein stop at a walk until it\'s automatic.', 'Progress to trot in a safe enclosed arena before open spaces.', 'Systematic desensitization to triggers that cause the bolt.', 'Work with a trainer on a conditioning program for the stop.'],
    barn_sour: ['Identify whether horse is barn sour or buddy sour — the fix differs.', 'Practice leaving the barn/buddy for very short distances, rewarding calm.', 'Gradually increase distance; never return when horse is anxious — wait for calm.', 'Develop forward on the ground before riding.', 'Make the barn "boring" — long waits tied before and after rides.'],
    spooky: ['Begin a systematic desensitization program on the ground.', 'Introduce scary objects at distance, moving closer only when horse is relaxed.', 'Build a relaxation cue — a breath, a word, a pat — and reinforce it.', 'Expose horse to new environments gradually and positively.', 'Progress to mounted desensitization once ground confidence is solid.'],
    wont_load: ['Set up the trailer in a low-stress location — open both doors, no pressure.', 'Reward every try toward the trailer, no matter how small.', 'Allow horse to investigate at its own pace over multiple sessions.', 'Never force — loading under force creates a worse problem.', 'Progress from front feet in → all in → short rides → longer trips.'],
    reining: ['Establish solid forward and rhythm before collection.', 'Build a quiet, reliable stop from the walk before loping.', 'Develop circles — large/fast, small/slow — with consistent speed.', 'Work on lead changes after circles are solid.', 'Spinning and rollbacks are the last maneuvers added — foundation first.'],
    barrel_racing: ['Establish a horse that rates, collects, and drives forward on cue.', 'Walk the pattern perfectly before any speed work.', 'Trot the pattern consistently before adding the lope.', 'Work individual barrels before running full pattern.', 'Condition and fitness program is as important as pattern work.'],
    dressage: ['Begin with the Training Scale: Rhythm → Relaxation → Contact.', 'Establish forward, straight movement at all gaits.', 'Introduce lateral work: leg yields before shoulder-in.', 'Collection comes from strength and engagement, not pulling on the reins.', 'Transition work is the foundation of all upper-level work.'],
    colt_starting: ['Complete all groundwork before first ride — yielding, backing, desensitizing.', 'First saddling: desensitize to blanket and pad first, then girth slowly.', 'First ride should be in a safe enclosed round pen or small arena.', 'Focus on steering and forward in the first 30 days.', 'Build in rest days — young horses need time to process.'],
    groundwork: ['Start with halter pressure and release — horse must learn to yield to pressure.', 'Yielding hindquarters and forequarters are the foundation of everything.', 'Add backing from the ground before expecting it under saddle.', 'Lunging teaches pace, direction, and voice commands.', 'Desensitization should be ongoing throughout training.'],
    trail: ['Build confidence in a controlled environment before hitting the trail.', 'Introduce obstacles on the ground first — tarps, bridges, water.', 'Ride with a calm, experienced horse as a guide horse early on.', 'Don\'t overface the horse — short, positive rides beat long stressful ones.', 'Practice the unexpected: calmly expose to bikes, dogs, plastic bags.'],
    mustang: ['Trust and approach are everything in week one — let horse acclimate.', 'All early work is pressure and release — remove pressure for any try.', 'Halter training comes before any other handling.', 'Do not rush — mustangs learn from pressure removal, not from force.', 'Each horse is different — some progress in days, others need weeks at each step.'],
  };

  // Get pathway by first problem or discipline
  const key = problems[0] || discipline || 'groundwork';
  return pathways[key] || pathways.groundwork;
}

// ── AI CALL ───────────────────────────────────────────────────
async function callAI(intakeData) {
  const prompt = `
You are the HorseTrainer.ai Training Assistant. A user has submitted the following intake data:
- Discipline: ${intakeData.discipline || 'general'}
- Horse Age: ${intakeData.horse_age || 'unknown'}
- Training Situation: ${intakeData.training_situation || 'general improvement'}
- Problems: ${(intakeData.problems || []).join(', ') || 'none specified'}
- Danger Rating: ${intakeData.danger_rating}/5
- Rider Level: ${intakeData.rider_level || 'unknown'}
- State: ${intakeData.state || 'unspecified'}

Provide a 2-sentence situation summary only. Be practical, horse-person language. No fluff. Do not add training steps — those come from the system. Just the summary.
`;

  try {
    const res = await fetch(CONFIG.WORKER_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt }),
    });
    if (!res.ok) throw new Error('Worker error');
    const data = await res.json();
    return data.summary || null;
  } catch (e) {
    return null; // Fall back to local summary
  }
}

function generateLocalSummary(data) {
  const disc = (data.discipline || 'general').replace(/_/g, ' ');
  const prob = data.problems?.length ? data.problems[0].replace(/_/g, ' ') : null;
  const age = data.horse_age || 'your horse';
  const sit = data.training_situation || 'training';

  if (prob) {
    return `Based on your intake, ${age} is presenting a ${prob} problem in a ${disc} context. This is a structured, solvable issue — here's how to approach it systematically.`;
  }
  if (data.training_situation === 'starting_young') {
    return `You're starting a ${age} horse in ${disc} — one of the most important phases of a horse's training life. A strong foundation now pays dividends for years.`;
  }
  return `Your ${age} horse is working in ${disc} and you're focused on ${sit.replace(/_/g, ' ')}. Here's a structured training pathway to move forward effectively.`;
}

// ── INTAKE UI ─────────────────────────────────────────────────
function initIntake() {
  const modal = document.getElementById('intake-modal');
  const overlay = document.getElementById('intake-overlay');
  if (!modal || !overlay) return;

  // Open triggers
  document.querySelectorAll('[data-open-intake]').forEach(el => {
    el.addEventListener('click', () => {
      const disc = el.dataset.discipline;
      if (disc) intakeState.data.discipline = disc;
      openIntake();
    });
  });

  // Close
  document.getElementById('intake-close')?.addEventListener('click', closeIntake);
  overlay.addEventListener('click', e => { if (e.target === overlay) closeIntake(); });

  // Option buttons
  modal.addEventListener('click', e => {
    const btn = e.target.closest('[data-opt]');
    if (!btn) return;
    const field = btn.dataset.field;
    const val   = btn.dataset.opt;
    const multi = btn.dataset.multi === 'true';

    if (multi) {
      if (intakeState.data[field].includes(val)) {
        intakeState.data[field] = intakeState.data[field].filter(v => v !== val);
        btn.classList.remove('selected');
      } else {
        intakeState.data[field].push(val);
        btn.classList.add('selected');
      }
    } else {
      // Single select: deselect siblings
      modal.querySelectorAll(`[data-field="${field}"]`).forEach(b => b.classList.remove('selected'));
      intakeState.data[field] = val;
      btn.classList.add('selected');
    }
  });

  // Danger slider
  const slider = document.getElementById('danger-slider');
  const sliderVal = document.getElementById('danger-value');
  if (slider) {
    slider.addEventListener('input', () => {
      intakeState.data.danger_rating = parseInt(slider.value);
      const labels = ['', 'Safe', 'Mild issue', 'Moderate', 'Dangerous', 'Very dangerous'];
      if (sliderVal) sliderVal.textContent = `${slider.value}/5 — ${labels[slider.value]}`;
    });
  }

  // Text inputs
  modal.querySelectorAll('[data-bind]').forEach(el => {
    el.addEventListener('input', () => {
      intakeState.data[el.dataset.bind] = el.value;
    });
    el.addEventListener('change', () => {
      intakeState.data[el.dataset.bind] = el.value;
    });
  });

  // Nav buttons
  document.getElementById('intake-next')?.addEventListener('click', nextStep);
  document.getElementById('intake-back')?.addEventListener('click', prevStep);

  updateStepUI();
}

function openIntake() {
  const overlay = document.getElementById('intake-overlay');
  if (overlay) { overlay.classList.add('open'); document.body.style.overflow = 'hidden'; }
  // Reset to step 1
  intakeState.currentStep = 1;
  intakeState.data = { discipline: intakeState.data.discipline, horse_age: null, training_situation: null, problems: [], danger_rating: 2, rider_level: null, state: null, zip: null, travel_radius: '50', budget: null, online_ok: false };
  updateStepUI();
}

function closeIntake() {
  const overlay = document.getElementById('intake-overlay');
  if (overlay) { overlay.classList.remove('open'); document.body.style.overflow = ''; }
  const aiResult = document.getElementById('ai-result');
  if (aiResult) aiResult.classList.add('hidden');
  const intakeBody = document.getElementById('intake-body');
  if (intakeBody) intakeBody.classList.remove('hidden');
}

function nextStep() {
  if (intakeState.currentStep < intakeState.totalSteps) {
    intakeState.currentStep++;
    updateStepUI();
  } else {
    submitIntake();
  }
}

function prevStep() {
  if (intakeState.currentStep > 1) {
    intakeState.currentStep--;
    updateStepUI();
  }
}

function updateStepUI() {
  const step = intakeState.currentStep;
  const total = intakeState.totalSteps;

  // Progress
  const fill = document.getElementById('progress-fill');
  const label = document.getElementById('step-label');
  if (fill) fill.style.width = `${(step / total) * 100}%`;
  if (label) label.textContent = `Step ${step} of ${total}`;

  // Show correct step
  document.querySelectorAll('.intake-step').forEach(s => s.classList.remove('active'));
  const current = document.getElementById(`step-${step}`);
  if (current) current.classList.add('active');

  // Back button
  const back = document.getElementById('intake-back');
  if (back) back.style.visibility = step === 1 ? 'hidden' : 'visible';

  // Next button label
  const next = document.getElementById('intake-next');
  if (next) next.textContent = step === total ? 'Get My Training Plan →' : 'Next →';
}

async function submitIntake() {
  const body = document.getElementById('intake-body');
  const result = document.getElementById('ai-result');
  if (!body || !result) return;

  body.classList.add('hidden');
  result.classList.remove('hidden');

  const loading = document.getElementById('ai-loading');
  const content = document.getElementById('ai-content');
  if (loading) loading.classList.remove('hidden');
  if (content) content.classList.add('hidden');

  // Risk evaluation
  const risk = RISK_RULES.evaluate(intakeState.data);

  // AI call (with fallback)
  const summary = await callAI(intakeState.data) || generateLocalSummary(intakeState.data);

  // Trainer category
  const trainerCat = getTrainerCategory(intakeState.data);

  // Related pages
  const relatedPages = getRelatedPages(intakeState.data);

  // Pathway (only if not red)
  const pathway = risk.level !== 'red' ? generateLocalPathway(intakeState.data) : null;

  // Render
  if (loading) loading.classList.add('hidden');
  if (content) {
    content.classList.remove('hidden');
    renderAIResult(content, { summary, risk, pathway, trainerCat, relatedPages });
  }

  // Log to Supabase (non-blocking)
  logIntakeSession(intakeState.data, risk.level).catch(() => {});
}

function renderAIResult(container, { summary, risk, pathway, trainerCat, relatedPages }) {
  const riskBadge = { green: '🟢 Self-Guided Safe', yellow: '🟡 Trainer Consult Recommended', red: '🔴 Professional Required' }[risk.level];
  const riskClass = { green: 'badge-green', yellow: 'badge-yellow', red: 'badge-red' }[risk.level];
  const riskBannerClass = `risk-${risk.level}`;

  let pathwayHTML = '';
  if (pathway && pathway.length) {
    pathwayHTML = `
      <div class="ai-section">
        <div class="ai-section-label">Training Pathway</div>
        <ol class="ai-steps">
          ${pathway.map((step, i) => `
            <li>
              <span class="ai-step-num">${i + 1}</span>
              <span>${step}</span>
            </li>
          `).join('')}
        </ol>
      </div>`;
  }

  let painHTML = '';
  if (risk.pain_flag) {
    painHTML = `
      <div class="risk-banner risk-yellow" style="margin-bottom:1rem;">
        <span class="risk-icon">⚠️</span>
        <div>
          <strong>Rule Out Pain First</strong>
          <p>Before training, eliminate saddle fit issues, dental problems, back soreness, and lameness as causes. Have your vet and a certified saddle fitter evaluate before proceeding.</p>
        </div>
      </div>`;
  }

  let riskMessages = '';
  if (risk.messages.length) {
    riskMessages = `
      <div class="risk-banner ${riskBannerClass}" style="margin-bottom:1rem;">
        <span class="risk-icon">${risk.level === 'red' ? '🚨' : '⚠️'}</span>
        <div>${risk.messages.map(m => `<p>${m}</p>`).join('')}</div>
      </div>`;
  }

  let relatedHTML = '';
  if (relatedPages.length) {
    relatedHTML = `
      <div class="ai-section">
        <div class="ai-section-label">Related Articles</div>
        <div class="ai-page-links">
          ${relatedPages.map(p => `
            <a href="${p.url}" class="ai-page-link" target="_blank">
              <span>📄</span> ${p.title} <span class="arrow">→</span>
            </a>
          `).join('')}
        </div>
      </div>`;
  }

  container.innerHTML = `
    <div class="ai-response">
      <div class="ai-response-header">
        <div class="ai-avatar">🐎</div>
        <div>
          <div class="ai-response-title">Your Training Assessment</div>
          <div class="ai-response-sub">Based on your answers · Not a replacement for a professional</div>
        </div>
      </div>

      <span class="badge ${riskClass}" style="margin-bottom:1rem;">${riskBadge}</span>

      <div class="ai-section">
        <p style="color:var(--cream-dim);font-size:0.95rem;line-height:1.65;">${summary}</p>
      </div>

      ${riskMessages}
      ${painHTML}
      ${pathwayHTML}
      ${relatedHTML}

      <div class="ai-section" style="margin-top:1.25rem;padding-top:1.25rem;border-top:1px solid var(--border);">
        <div class="ai-section-label">Recommended Trainer Type</div>
        <p style="margin-bottom:0.875rem;color:var(--cream-dim);font-size:0.9rem;">
          Based on your situation, we recommend connecting with a <strong style="color:var(--cream);">${trainerCat.label}</strong>.
        </p>
        <a href="${trainerCat.url}" class="btn btn-primary btn-full">
          Find a ${trainerCat.label} →
        </a>
      </div>

      <p style="font-size:0.72rem;color:var(--muted);margin-top:1rem;text-align:center;line-height:1.5;">
        HorseTrainer.ai provides educational guidance only. Always consult a professional trainer, veterinarian, or farrier for your specific situation.
      </p>
    </div>
  `;
}

// ── SUPABASE LOGGING ──────────────────────────────────────────
async function logIntakeSession(data, risk_level) {
  if (!CONFIG.SUPABASE_URL || CONFIG.SUPABASE_URL.includes('YOUR_')) return;
  await fetch(`${CONFIG.SUPABASE_URL}/rest/v1/intake_sessions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'apikey': CONFIG.SUPABASE_ANON,
      'Authorization': `Bearer ${CONFIG.SUPABASE_ANON}`,
      'Prefer': 'return=minimal',
    },
    body: JSON.stringify({
      intake_data: data,
      risk_level,
      discipline: data.discipline,
    }),
  });
}

// ── TRAINER MATCHER ────────────────────────────────────────────
async function loadTrainers(filters = {}) {
  if (!CONFIG.SUPABASE_URL || CONFIG.SUPABASE_URL.includes('YOUR_')) {
    return getDemoTrainers();
  }
  let url = `${CONFIG.SUPABASE_URL}/rest/v1/trainers?select=*&active=eq.true`;
  if (filters.state) url += `&state=eq.${filters.state}`;
  const res = await fetch(url, {
    headers: { 'apikey': CONFIG.SUPABASE_ANON, 'Authorization': `Bearer ${CONFIG.SUPABASE_ANON}` },
  });
  if (!res.ok) return getDemoTrainers();
  return res.json();
}

function scoreTrainer(trainer, matchData) {
  let score = 0;
  const { discipline, problems = [], danger_rating = 1, rider_level, state, budget, online_ok } = matchData;

  // Discipline match (25 pts)
  if (trainer.disciplines?.includes(discipline)) score += 25;
  else if (trainer.disciplines?.some(d => isRelatedDiscipline(d, discipline))) score += 15;

  // Problem/specialty match (20 pts)
  if (danger_rating >= 4 && !trainer.accepts_dangerous) return -1; // disqualify
  if (problems.length) {
    const problemMatch = problems.some(p => trainer.horse_problems?.includes(p) || trainer.specialties?.includes(p));
    if (problemMatch) score += 20;
  }
  if (danger_rating >= 4 && trainer.accepts_dangerous) score += 5;

  // Location (15 pts)
  if (state && trainer.state === state) score += 15;
  else if (state && isAdjacentState(trainer.state, state)) score += 6;
  if (online_ok && trainer.online_coaching) score += 10;

  // Rider level (10 pts)
  if (trainer.rider_levels?.includes(rider_level)) score += 10;

  // Budget (10 pts)
  if (budget && trainer.budget_range === budget) score += 10;
  else if (budget) score += 5;

  // VIP score (10 pts)
  score += Math.round((trainer.vip_score || 0) / 10);

  // Listing tier bonus
  const tierBonus = { featured: 5, vip: 3, basic: 1, free: 0 };
  score += tierBonus[trainer.listing_tier] || 0;

  return score;
}

function isRelatedDiscipline(a, b) {
  const groups = [
    ['reining','cutting','working_cow','ranch'],
    ['roping','ranch'],
    ['hunter_jumper','eventing','equitation'],
    ['dressage','eventing'],
    ['colt_starting','groundwork','mustang'],
    ['trail','groundwork'],
  ];
  return groups.some(g => g.includes(a) && g.includes(b));
}

function isAdjacentState(a, b) {
  const adj = { AZ: ['NM','NV','UT','CA','CO'], TX: ['NM','OK','AR','LA'], CO: ['WY','NE','KS','OK','NM','AZ','UT'] };
  return adj[a]?.includes(b) || adj[b]?.includes(a);
}

function renderTrainerCards(trainers, container) {
  if (!container) return;
  if (!trainers.length) {
    container.innerHTML = '<p style="color:var(--muted);text-align:center;padding:2rem;">No trainers found matching your criteria. Try expanding your search radius or browse all trainers.</p>';
    return;
  }
  container.innerHTML = trainers.map(t => trainerCardHTML(t)).join('');
}

function trainerCardHTML(t) {
  const tags = [...(t.disciplines || []).slice(0, 2), ...(t.specialties || []).slice(0, 1)]
    .map(tag => `<span class="badge badge-muted">${tag.replace(/_/g, ' ')}</span>`).join('');
  const score = t._score;
  const matchLabel = score >= 80 ? 'Strong Match' : score >= 60 ? 'Good Match' : 'Possible Match';
  const scoreHTML = score !== undefined ? `
    <div class="match-score">
      <span>${matchLabel}</span>
      <div class="match-score-bar"><div class="match-score-fill" style="width:${score}%"></div></div>
      <span>${score}%</span>
    </div>` : '';
  const vipBadge = t.vip ? '<span class="badge badge-gold">⭐ VIP</span>' : '';
  const onlineBadge = t.online_coaching ? '<span class="badge badge-muted">🖥 Online</span>' : '';

  return `
    <div class="trainer-card">
      <div class="trainer-card-header">
        <div class="trainer-avatar">
          ${t.photo_url ? `<img src="${t.photo_url}" alt="${t.name}" loading="lazy">` : '🤠'}
        </div>
        <div class="trainer-info">
          <div class="trainer-name">${t.name}</div>
          <div class="trainer-location">📍 ${t.city}, ${t.state}</div>
          <div style="display:flex;gap:0.4rem;flex-wrap:wrap;margin-top:0.4rem;">${vipBadge}${onlineBadge}</div>
        </div>
      </div>
      <div class="trainer-card-body">
        <div class="trainer-tags">${tags}</div>
        ${t.bio ? `<div class="trainer-bio">${t.bio}</div>` : ''}
        ${scoreHTML}
      </div>
      <div class="trainer-card-footer">
        <a href="/trainers/${t.slug}/" class="btn btn-outline btn-sm" style="flex:1;">View Profile</a>
        <a href="/trainers/${t.slug}/#contact" class="btn btn-primary btn-sm" style="flex:1;">Contact</a>
      </div>
    </div>
  `;
}

// ── DEMO DATA (shown when Supabase not configured) ────────────
function getDemoTrainers() {
  return [
    { id: '1', name: 'Wade Callahan', slug: 'wade-callahan', city: 'Scottsdale', state: 'AZ', disciplines: ['reining','colt_starting'], specialties: ['problem_horse'], horse_problems: ['bucking','bolting'], rider_levels: ['intermediate','advanced'], bio: '20+ years starting colts and correcting problem horses across the Southwest. NRHA Professional. No problem too big.', vip: true, vip_score: 90, listing_tier: 'featured', online_coaching: false, accepts_dangerous: true, budget_range: 'mid', photo_url: null },
    { id: '2', name: 'Shelly Raines', slug: 'shelly-raines', city: 'Tucson', state: 'AZ', disciplines: ['barrel_racing','trail'], specialties: ['youth_coach'], horse_problems: ['barn_sour','spooky'], rider_levels: ['beginner','intermediate'], bio: 'Specializing in barrel prospects and youth riders. NBHA member. Building confidence in horse and rider for 15 years.', vip: true, vip_score: 78, listing_tier: 'vip', online_coaching: true, accepts_dangerous: false, budget_range: 'budget', photo_url: null },
    { id: '3', name: 'R.D. Harmon', slug: 'rd-harmon', city: 'Prescott', state: 'AZ', disciplines: ['cutting','working_cow','ranch'], specialties: ['colt_starting'], horse_problems: [], rider_levels: ['intermediate','advanced','professional'], bio: 'Third-generation cowboy. NCHA member. Cutting, cow horse, and ranch horses trained from the ground up.', vip: false, vip_score: 65, listing_tier: 'basic', online_coaching: false, accepts_dangerous: false, budget_range: 'mid', photo_url: null },
    { id: '4', name: 'Claire Ashworth', slug: 'claire-ashworth', city: 'Chandler', state: 'AZ', disciplines: ['dressage','hunter_jumper','equitation'], specialties: ['youth_coach','online'], horse_problems: ['refusing_jumps'], rider_levels: ['beginner','intermediate','advanced'], bio: 'USEF Certified instructor. Training English disciplines from Intro through Third Level. Online video review available.', vip: false, vip_score: 72, listing_tier: 'vip', online_coaching: true, accepts_dangerous: false, budget_range: 'mid', photo_url: null },
  ];
}

// ── MATCH PAGE ────────────────────────────────────────────────
function initMatchPage() {
  const form = document.getElementById('match-form');
  if (!form) return;

  form.addEventListener('submit', async e => {
    e.preventDefault();
    const matchData = {
      discipline: form.querySelector('[name=discipline]')?.value,
      horse_age: form.querySelector('[name=horse_age]')?.value,
      training_situation: form.querySelector('[name=situation]')?.value,
      problems: Array.from(form.querySelectorAll('[name=problems]:checked')).map(cb => cb.value),
      danger_rating: parseInt(form.querySelector('[name=danger]')?.value || 2),
      rider_level: form.querySelector('[name=rider_level]')?.value,
      state: form.querySelector('[name=state]')?.value,
      budget: form.querySelector('[name=budget]')?.value,
      online_ok: form.querySelector('[name=online_ok]')?.checked,
    };

    const resultsContainer = document.getElementById('match-results');
    const resultsSection = document.getElementById('results-section');
    if (resultsContainer) resultsContainer.innerHTML = '<div class="ai-loading"><div class="ai-loading-dots"><span></span><span></span><span></span></div> Finding your best trainer matches...</div>';
    if (resultsSection) resultsSection.scrollIntoView({ behavior: 'smooth' });

    try {
      const trainers = await loadTrainers({ state: matchData.state });
      const scored = trainers
        .map(t => ({ ...t, _score: scoreTrainer(t, matchData) }))
        .filter(t => t._score >= 30)
        .sort((a, b) => b._score - a._score)
        .slice(0, 6);

      renderTrainerCards(scored, resultsContainer);
    } catch (err) {
      const demos = getDemoTrainers().map(t => ({ ...t, _score: Math.floor(Math.random() * 30) + 65 }));
      renderTrainerCards(demos, resultsContainer);
    }
  });
}

// ── LEAD CAPTURE ──────────────────────────────────────────────
function initLeadForms() {
  document.querySelectorAll('[data-lead-form]').forEach(form => {
    form.addEventListener('submit', async e => {
      e.preventDefault();
      const btn = form.querySelector('[type=submit]');
      const orig = btn?.textContent;
      if (btn) { btn.textContent = 'Sending...'; btn.disabled = true; }

      const data = {
        trainer_id: form.dataset.trainerId || null,
        name: form.querySelector('[name=name]')?.value,
        email: form.querySelector('[name=email]')?.value,
        phone: form.querySelector('[name=phone]')?.value,
        message: form.querySelector('[name=message]')?.value,
        discipline: form.querySelector('[name=discipline]')?.value,
      };

      try {
        if (CONFIG.SUPABASE_URL && !CONFIG.SUPABASE_URL.includes('YOUR_')) {
          await fetch(`${CONFIG.SUPABASE_URL}/rest/v1/leads`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'apikey': CONFIG.SUPABASE_ANON,
              'Authorization': `Bearer ${CONFIG.SUPABASE_ANON}`,
              'Prefer': 'return=minimal',
            },
            body: JSON.stringify(data),
          });
        }
        form.innerHTML = '<div class="risk-banner risk-green" style="margin:0;"><span class="risk-icon">✅</span><div><strong>Message Sent!</strong><p>The trainer will be in touch shortly. Check your email for confirmation.</p></div></div>';
      } catch (err) {
        if (btn) { btn.textContent = orig; btn.disabled = false; }
        alert('Something went wrong. Please try again.');
      }
    });
  });
}

// ── NAVIGATION ────────────────────────────────────────────────
function initNav() {
  const nav = document.querySelector('.nav');
  const menuBtn = document.getElementById('nav-menu-btn');
  const drawer = document.getElementById('nav-drawer');

  if (nav) {
    window.addEventListener('scroll', () => {
      nav.classList.toggle('scrolled', window.scrollY > 20);
    }, { passive: true });
  }

  if (menuBtn && drawer) {
    menuBtn.addEventListener('click', () => {
      const open = drawer.classList.toggle('open');
      document.body.style.overflow = open ? 'hidden' : '';
    });
  }

  // Close drawer on link click
  drawer?.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', () => {
      drawer.classList.remove('open');
      document.body.style.overflow = '';
    });
  });

  // Highlight current page
  const path = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(link => {
    if (link.getAttribute('href') === path) link.classList.add('active');
  });
}

// ── FADE-IN ANIMATIONS ────────────────────────────────────────
function initAnimations() {
  if (!('IntersectionObserver' in window)) {
    document.querySelectorAll('.fade-up').forEach(el => el.classList.add('visible'));
    return;
  }
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('visible'); obs.unobserve(e.target); } });
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

  document.querySelectorAll('.fade-up').forEach(el => obs.observe(el));
}

// ── DISCIPLINE FILTER ─────────────────────────────────────────
function initDisciplineFilter() {
  const filterBtns = document.querySelectorAll('[data-filter]');
  const filterable = document.querySelectorAll('[data-disc]');
  if (!filterBtns.length) return;

  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');
      const filter = btn.dataset.filter;
      filterable.forEach(el => {
        el.style.display = filter === 'all' || el.dataset.disc === filter ? '' : 'none';
      });
    });
  });
}

// ── INIT ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initNav();
  initIntake();
  initMatchPage();
  initLeadForms();
  initAnimations();
  initDisciplineFilter();
});
