/**
 * fal.ai Video Pipeline Command Center - Interactive Controller
 */

document.addEventListener('DOMContentLoaded', () => {
  // State variables
  let currentJobs = [];
  let selectedJob = null;
  let activeWizardStep = 1;
  let pollIntervalId = null;

  // Niche topic recommendations data
  const NICHE_TOPICS = {
    "Sci-Fi Lore": [
      { title: "The Dyson Singularity", keyword: "Megastructure Collapse" },
      { title: "Neo-Tokyo 2099", keyword: "Cybernetic Underworld" },
      { title: "Echoes of Kepler-186f", keyword: "Exoplanet Biosphere" },
      { title: "Chronos Protocol", keyword: "Temporal Paradox Engine" }
    ],
    "Tech Breakdown": [
      { title: "Quantum Supercomputing 101", keyword: "Qubit Entanglement" },
      { title: "Autonomous Humanoid Robotics", keyword: "Actuator Precision" },
      { title: "Next-Gen Nuclear Fusion", keyword: "Tokamak Confinement" },
      { title: "Neural Interfaces Explained", keyword: "Direct Brain-Computer Link" }
    ],
    "True Crime & Mystery": [
      { title: "The Vanishing of Flight 812", keyword: "Radar Anomaly" },
      { title: "The Blackwood Manor Cipher", keyword: "Coded Diary Entries" },
      { title: "Midnight at the Harbor", keyword: "Unsolved Heist" }
    ],
    "Dark Fantasy": [
      { title: "Tears of the Eclipse King", keyword: "Forgotten Bloodlines" },
      { title: "Shadows Over Valdor", keyword: "Forbidden Grimoires" },
      { title: "The Hollow Titan", keyword: "Ancient Colossi" }
    ],
    "History Uncovered": [
      { title: "The Secret Vaults of Alexandria", keyword: "Lost Papyrus Scrolls" },
      { title: "The Siege of Constantinople", keyword: "The Golden Horn Defense" },
      { title: "Forgotten Samurai Legends", keyword: "Feudal Battlefield Honor" }
    ],
    "Mindset & Wealth": [
      { title: "The 1% Focus Formula", keyword: "Deep Flow State" },
      { title: "Asymmetric Risk in Investing", keyword: "Exponential Compound Returns" },
      { title: "The Stoic Blueprint", keyword: "Emotional Resilience" }
    ],
    "Cosmic Horror": [
      { title: "The Voice From the Abyss", keyword: "Sub-Oceanic Monolith" },
      { title: "Signal From Dark Matter", keyword: "Cosmic Whispers" }
    ]
  };

  // =========================================================================
  // 1. Web Audio API Success Chime Synthesizer
  // =========================================================================

  function playSuccessChime() {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();

      const now = ctx.currentTime;
      
      // Dual-tone harmonic chime (C5 + G5)
      const freqs = [523.25, 783.99]; 
      freqs.forEach((freq, idx) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, now + idx * 0.08);

        gain.gain.setValueAtTime(0, now + idx * 0.08);
        gain.gain.linearRampToValueAtTime(0.2, now + idx * 0.08 + 0.04);
        gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.08 + 1.2);

        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.start(now + idx * 0.08);
        osc.stop(now + idx * 0.08 + 1.3);
      });
    } catch (e) {
      console.warn("Web Audio chime failed:", e);
    }
  }

  // =========================================================================
  // 2. Theme Management (Dark / Light)
  // =========================================================================

  const themeToggleBtn = document.getElementById('btn-theme-toggle');
  const themeIcon = document.getElementById('theme-icon');

  function initTheme() {
    const savedTheme = localStorage.getItem('fal_theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    themeIcon.textContent = savedTheme === 'dark' ? '🌙' : '☀️';
  }

  themeToggleBtn.addEventListener('click', () => {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('fal_theme', newTheme);
    themeIcon.textContent = newTheme === 'dark' ? '🌙' : '☀️';
  });

  initTheme();

  // =========================================================================
  // 3. Tabs Navigation
  // =========================================================================

  const tabButtons = document.querySelectorAll('.tab-btn');
  const tabPanes = document.querySelectorAll('.tab-pane');

  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      tabButtons.forEach(b => b.classList.remove('active'));
      tabPanes.forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      const targetPane = document.getElementById(btn.dataset.tab);
      if (targetPane) {
        targetPane.classList.add('active');
      }

      if (btn.dataset.tab === 'tab-jobs') {
        fetchJobs();
      } else if (btn.dataset.tab === 'tab-diagnostics') {
        fetchDiagnostics();
      }
    });
  });

  // =========================================================================
  // 4. Form Helpers, Dynamic Suggestions & Word Count Sync
  // =========================================================================

  const selectNiche = document.getElementById('select-niche');
  const inputTitle = document.getElementById('input-title');
  const inputKeyword = document.getElementById('input-keyword');
  const rangeDuration = document.getElementById('range-duration');
  const durationValDisplay = document.getElementById('duration-val-display');
  const wordCountCalc = document.getElementById('word-count-calc');
  const nicheSuggestionsContainer = document.getElementById('niche-suggestions-container');
  const countTitle = document.getElementById('count-title');
  const inputScript = document.getElementById('input-script');
  const countScript = document.getElementById('count-script');

  // Sync Duration Range with Live Word Count (~2.5 words per sec)
  function updateDurationDisplay(val) {
    durationValDisplay.textContent = `${val}s`;
    const estWords = Math.round(val * 2.5);
    wordCountCalc.textContent = `~${estWords} words (${Math.round(val / 10)} shots)`;
    document.getElementById('summary-duration').textContent = `${val}s (~${Math.round(val / 10)} Shots)`;
  }

  rangeDuration.addEventListener('input', (e) => {
    updateDurationDisplay(e.target.value);
  });
  updateDurationDisplay(rangeDuration.value);

  // Character counters
  inputTitle.addEventListener('input', () => {
    countTitle.textContent = `${inputTitle.value.length} / 150`;
    document.getElementById('summary-title').textContent = inputTitle.value || 'Untitled Production';
  });

  inputScript.addEventListener('input', () => {
    countScript.textContent = `${inputScript.value.length} chars`;
  });

  // Render Dynamic Niche Suggestions
  function renderNicheSuggestions(nicheName, container, titleInput, keywordInput) {
    container.innerHTML = '';
    const topics = NICHE_TOPICS[nicheName] || NICHE_TOPICS["Sci-Fi Lore"];
    topics.forEach(topic => {
      const chip = document.createElement('button');
      chip.type = 'button';
      chip.className = 'suggestion-chip';
      chip.textContent = `✨ ${topic.title} (${topic.keyword})`;
      chip.addEventListener('click', () => {
        titleInput.value = topic.title;
        keywordInput.value = topic.keyword;
        titleInput.dispatchEvent(new Event('input'));
        showToast(`Applied topic: "${topic.title}"`, 'success');
      });
      container.appendChild(chip);
    });
  }

  selectNiche.addEventListener('change', () => {
    renderNicheSuggestions(selectNiche.value, nicheSuggestionsContainer, inputTitle, inputKeyword);
    document.getElementById('summary-niche').textContent = selectNiche.value;
  });
  renderNicheSuggestions(selectNiche.value, nicheSuggestionsContainer, inputTitle, inputKeyword);

  // Demographic preset chips
  const demographicChips = document.querySelectorAll('#demographic-presets .chip');
  const inputDemographic = document.getElementById('input-demographic');
  demographicChips.forEach(chip => {
    chip.addEventListener('click', () => {
      demographicChips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      inputDemographic.value = chip.dataset.val;
      document.getElementById('summary-demographic').textContent = chip.dataset.val;
    });
  });

  // Visual Style change summary
  const selectStyle = document.getElementById('select-style');
  selectStyle.addEventListener('change', () => {
    document.getElementById('summary-style').textContent = selectStyle.value;
  });

  // Voice Tone summary
  const selectVoiceTone = document.getElementById('select-voice-tone');
  selectVoiceTone.addEventListener('change', () => {
    document.getElementById('summary-voice').textContent = selectVoiceTone.value;
  });

  // Template helper autofills
  document.querySelectorAll('.helper-chip').forEach(btn => {
    btn.addEventListener('click', () => {
      const targetInput = document.getElementById(btn.dataset.target);
      if (targetInput) {
        let text = btn.dataset.text;
        const curTitle = inputTitle.value.trim() || 'Neo-Kyoto';
        const curKeyword = inputKeyword.value.trim() || 'the singularity';
        text = text.replace('{title}', curTitle).replace('{keyword}', curKeyword);
        targetInput.value = text;
        showToast('Template hook applied!', 'success');
      }
    });
  });

  // =========================================================================
  // 5. Video Generation Submission & Pipeline API
  // =========================================================================

  const formProduction = document.getElementById('video-production-form');
  const btnSubmitJob = document.getElementById('btn-submit-job');

  formProduction.addEventListener('submit', async (e) => {
    e.preventDefault();
    btnSubmitJob.disabled = true;
    btnSubmitJob.innerHTML = '<span class="btn-icon">⏳</span> Dispatching Production...';

    const payload = {
      title: inputTitle.value.trim() || "Untitled Project",
      niche: selectNiche.value,
      focus_keyword: inputKeyword.value.trim() || null,
      visual_style: selectStyle.value,
      target_duration_sec: parseInt(rangeDuration.value, 10),
      target_demographic: inputDemographic.value,
      voice_tone: selectVoiceTone.value,
      recap_intro: document.getElementById('input-recap').value.trim() || null,
      custom_cliffhanger: document.getElementById('input-cliffhanger').value.trim() || null,
      full_script: inputScript.value.trim() || null,
      model_id: document.getElementById('select-model').value
    };

    try {
      const resp = await fetch('/api/jobs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!resp.ok) {
        const err = await resp.json();
        throw new Error(err.detail || 'Failed to submit job');
      }

      const job = await resp.json();
      showToast(`Job ${job.id} launched successfully!`, 'success');

      // Switch to jobs tab and open drawer
      const jobsTabBtn = document.querySelector('[data-tab="tab-jobs"]');
      jobsTabBtn.click();
      fetchJobs();
      openDrawer(job.id);
    } catch (err) {
      showToast(`Error launching production: ${err.message}`, 'error');
    } finally {
      btnSubmitJob.disabled = false;
      btnSubmitJob.innerHTML = '<span class="btn-icon">🚀</span> Launch Video Production';
    }
  });

  // =========================================================================
  // 6. Job History, Search, Polling & Registry
  // =========================================================================

  const tableBody = document.getElementById('jobs-table-body');
  const emptyState = document.getElementById('jobs-empty-state');
  const tableSearch = document.getElementById('table-search');
  const filterStatus = document.getElementById('filter-status');
  const btnRefreshJobs = document.getElementById('btn-refresh-jobs');
  const jobsCountBadge = document.getElementById('jobs-count-badge');

  async function fetchJobs() {
    try {
      const resp = await fetch('/api/jobs');
      if (!resp.ok) return;
      currentJobs = await resp.json();
      jobsCountBadge.textContent = currentJobs.length;
      renderJobsTable();
    } catch (e) {
      console.error("Failed to fetch jobs:", e);
    }
  }

  function renderJobsTable() {
    const query = (tableSearch.value || '').toLowerCase();
    const statusVal = filterStatus.value;

    const filtered = currentJobs.filter(job => {
      const matchStatus = !statusVal || job.status === statusVal;
      const matchQuery = !query ||
        (job.title && job.title.toLowerCase().includes(query)) ||
        (job.id && job.id.toLowerCase().includes(query)) ||
        (job.focus_keyword && job.focus_keyword.toLowerCase().includes(query)) ||
        (job.niche && job.niche.toLowerCase().includes(query));
      return matchStatus && matchQuery;
    });

    if (filtered.length === 0) {
      tableBody.innerHTML = '';
      emptyState.classList.remove('hidden');
      return;
    }

    emptyState.classList.add('hidden');
    tableBody.innerHTML = filtered.map(job => {
      const statusClass = `badge-${(job.status || 'queued').toLowerCase()}`;
      const createdDate = new Date(job.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

      return `
        <tr data-job-id="${job.id}" style="cursor: pointer;">
          <td>
            <strong>${escapeHtml(job.title || 'Untitled')}</strong><br>
            <span style="font-family: var(--font-mono); font-size: 0.75rem; color: var(--text-muted);">${job.id}</span>
          </td>
          <td>${escapeHtml(job.niche || 'General')}<br><small style="color: var(--text-muted);">${escapeHtml(job.focus_keyword || '')}</small></td>
          <td><span class="chip" style="padding: 2px 8px; font-size: 0.75rem;">${escapeHtml(job.visual_style || 'Cinematic')}</span></td>
          <td>${job.target_duration_sec || 60}s</td>
          <td><span class="badge ${statusClass}">${job.status}</span></td>
          <td>${createdDate}</td>
          <td>
            <button class="btn btn-ghost btn-sm btn-inspect-job" data-job-id="${job.id}">Inspect →</button>
          </td>
        </tr>
      `;
    }).join('');

    // Attach row click listeners
    tableBody.querySelectorAll('tr').forEach(row => {
      row.addEventListener('click', () => {
        openDrawer(row.dataset.jobId);
      });
    });
  }

  tableSearch.addEventListener('input', renderJobsTable);
  filterStatus.addEventListener('change', renderJobsTable);
  btnRefreshJobs.addEventListener('click', fetchJobs);

  // Background status poller for active jobs
  function startPolling() {
    if (pollIntervalId) clearInterval(pollIntervalId);
    pollIntervalId = setInterval(async () => {
      const hasActiveJobs = currentJobs.some(j => j.status === 'QUEUED' || j.status === 'IN_PROGRESS');
      if (hasActiveJobs) {
        const prevJobs = [...currentJobs];
        await fetchJobs();

        // Check if any job completed just now
        currentJobs.forEach(newJob => {
          const oldJob = prevJobs.find(p => p.id === newJob.id);
          if (oldJob && oldJob.status !== 'COMPLETED' && newJob.status === 'COMPLETED') {
            playSuccessChime();
            showToast(`🎉 Video production completed: "${newJob.title}"`, 'success');
            if (selectedJob && selectedJob.id === newJob.id) {
              openDrawer(newJob.id);
            }
          }
        });
      }
    }, 4000);
  }
  startPolling();

  // =========================================================================
  // 7. Slide-Out Details Drawer (.drawer)
  // =========================================================================

  const drawer = document.getElementById('job-details-drawer');
  const btnCloseDrawer = document.getElementById('btn-close-drawer');
  const drawerStatus = document.getElementById('drawer-job-status');
  const drawerTitle = document.getElementById('drawer-job-title');
  const drawerJobId = document.getElementById('drawer-job-id');
  const drawerVideoPlayer = document.getElementById('drawer-video-player');
  const drawerVideoSource = document.getElementById('drawer-video-source');
  const drawerScript = document.getElementById('drawer-script');
  const drawerTimeline = document.getElementById('drawer-timeline');
  const drawerSpecsGrid = document.getElementById('drawer-specs-grid');
  const drawerErrorSection = document.getElementById('drawer-error-section');
  const drawerErrorLog = document.getElementById('drawer-error-log');
  const btnDownloadJson = document.getElementById('btn-download-json');
  const btnRetryDrawerJob = document.getElementById('btn-retry-drawer-job');

  async function openDrawer(jobId) {
    try {
      const resp = await fetch(`/api/jobs/${jobId}`);
      if (!resp.ok) return;
      selectedJob = await resp.json();

      drawerTitle.textContent = selectedJob.title || 'Untitled';
      drawerJobId.textContent = selectedJob.id;
      drawerStatus.textContent = selectedJob.status;
      drawerStatus.className = `drawer-badge badge-${(selectedJob.status || '').toLowerCase()}`;

      // Video Player
      if (selectedJob.video_path) {
        drawerVideoSource.src = selectedJob.video_path;
        drawerVideoPlayer.load();
        document.getElementById('drawer-media-box').classList.remove('hidden');
      } else {
        document.getElementById('drawer-media-box').classList.add('hidden');
      }

      // Script
      drawerScript.textContent = selectedJob.full_script || 'No script generated.';

      // Timeline Visualizer
      const meta = selectedJob.metadata || {};
      const timeline = meta.timeline || [];
      if (timeline.length > 0) {
        drawerTimeline.innerHTML = timeline.map(shot => `
          <div class="timeline-item">
            <div class="timeline-meta">
              <span>Shot ${shot.shot_number}: ${shot.camera_movement || 'Cinematic'}</span>
              <span>${shot.timestamp_start}s - ${shot.timestamp_end}s (${shot.duration_sec}s)</span>
            </div>
            <p class="timeline-prompt">${escapeHtml(shot.visual_prompt)}</p>
          </div>
        `).join('');
      } else {
        drawerTimeline.innerHTML = '<p style="color: var(--text-muted); font-size: 0.85rem;">No timeline cues available.</p>';
      }

      // Specifications Grid
      drawerSpecsGrid.innerHTML = `
        <div class="spec-box"><strong>Niche:</strong> ${escapeHtml(selectedJob.niche || 'N/A')}</div>
        <div class="spec-box"><strong>Style:</strong> ${escapeHtml(selectedJob.visual_style || 'N/A')}</div>
        <div class="spec-box"><strong>Audience:</strong> ${escapeHtml(selectedJob.target_demographic || 'General')}</div>
        <div class="spec-box"><strong>Voice Tone:</strong> ${escapeHtml(selectedJob.voice_tone || 'Standard')}</div>
        <div class="spec-box"><strong>Duration:</strong> ${selectedJob.target_duration_sec}s</div>
        <div class="spec-box"><strong>Model:</strong> ${escapeHtml(selectedJob.model_id || 'Kling')}</div>
      `;

      // Error Log
      if (selectedJob.error_log) {
        drawerErrorSection.classList.remove('hidden');
        drawerErrorLog.textContent = selectedJob.error_log;
      } else {
        drawerErrorSection.classList.add('hidden');
      }

      // Freeze scroll on body
      document.body.classList.add('drawer-open');
    } catch (e) {
      console.error("Failed to load job details:", e);
    }
  }

  function closeDrawer() {
    document.body.classList.remove('drawer-open');
  }

  btnCloseDrawer.addEventListener('click', closeDrawer);

  // Playback speed controls
  document.querySelectorAll('.btn-speed').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.btn-speed').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const speed = parseFloat(btn.dataset.speed);
      drawerVideoPlayer.playbackRate = speed;
    });
  });

  // Download JSON metadata package
  btnDownloadJson.addEventListener('click', () => {
    if (!selectedJob) return;
    const blob = new Blob([JSON.stringify(selectedJob, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${selectedJob.id}_meta.json`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('Metadata package downloaded!', 'success');
  });

  // Retry job from drawer
  btnRetryDrawerJob.addEventListener('click', async () => {
    if (!selectedJob) return;
    try {
      const resp = await fetch(`/api/jobs/${selectedJob.id}/retry`, { method: 'POST' });
      if (!resp.ok) throw new Error('Retry failed');
      const updated = await resp.json();
      showToast(`Job ${updated.id} restarted!`, 'success');
      fetchJobs();
      openDrawer(updated.id);
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // =========================================================================
  // 8. Step-by-Step Onboarding Wizard Modal (#modal-wizard)
  // =========================================================================

  const modalWizard = document.getElementById('modal-wizard');
  const btnOpenWizard = document.getElementById('btn-open-wizard');
  const btnSidebarWizard = document.getElementById('btn-sidebar-wizard');
  const btnCloseWizard = document.getElementById('btn-close-wizard');
  const wizBtnPrev = document.getElementById('wiz-btn-prev');
  const wizBtnNext = document.getElementById('wiz-btn-next');
  const wizNiche = document.getElementById('wiz-niche');
  const wizTitle = document.getElementById('wiz-title');
  const wizKeyword = document.getElementById('wiz-keyword');
  const wizSuggestionsContainer = document.getElementById('wiz-suggestions-container');
  const wizVoiceTone = document.getElementById('wiz-voice-tone');
  const wizRangeDuration = document.getElementById('wiz-range-duration');
  const wizDurationVal = document.getElementById('wiz-duration-val');
  const wizWordCount = document.getElementById('wiz-word-count');

  let wizSelectedDemographic = 'General Audience';
  let wizSelectedStyle = 'Cinematic Photorealism';

  function openWizard() {
    activeWizardStep = 1;
    updateWizardUI();
    modalWizard.classList.add('open');
    document.body.classList.add('modal-open');
    renderNicheSuggestions(wizNiche.value, wizSuggestionsContainer, wizTitle, wizKeyword);
  }

  function closeWizard() {
    modalWizard.classList.remove('open');
    document.body.classList.remove('modal-open');
  }

  btnOpenWizard.addEventListener('click', openWizard);
  btnSidebarWizard.addEventListener('click', openWizard);
  btnCloseWizard.addEventListener('click', closeWizard);

  wizNiche.addEventListener('change', () => {
    renderNicheSuggestions(wizNiche.value, wizSuggestionsContainer, wizTitle, wizKeyword);
  });

  // Wizard Demographic Chips
  document.querySelectorAll('#wiz-demographics .chip').forEach(chip => {
    chip.addEventListener('click', () => {
      document.querySelectorAll('#wiz-demographics .chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      wizSelectedDemographic = chip.dataset.val;
    });
  });

  // Wizard Style Cards
  document.querySelectorAll('#wiz-style-grid .style-card').forEach(card => {
    card.addEventListener('click', () => {
      document.querySelectorAll('#wiz-style-grid .style-card').forEach(c => c.classList.remove('active'));
      card.classList.add('active');
      wizSelectedStyle = card.dataset.style;
    });
  });

  // Wizard Duration Slider
  wizRangeDuration.addEventListener('input', (e) => {
    const val = e.target.value;
    wizDurationVal.textContent = `${val}s`;
    wizWordCount.textContent = `~${Math.round(val * 2.5)} words`;
  });

  function updateWizardUI() {
    // Progress bar steps
    document.querySelectorAll('.wizard-progress-bar .progress-step').forEach(step => {
      const s = parseInt(step.dataset.step, 10);
      step.classList.toggle('active', s === activeWizardStep);
    });

    // Step panes
    document.querySelectorAll('.wizard-step-pane').forEach((pane, idx) => {
      pane.classList.toggle('active', idx + 1 === activeWizardStep);
    });

    wizBtnPrev.disabled = activeWizardStep === 1;
    wizBtnNext.textContent = activeWizardStep === 5 ? '🚀 Launch Production' : 'Next Step →';

    // Populate final summary on step 5
    if (activeWizardStep === 5) {
      document.getElementById('wiz-final-summary').innerHTML = `
        <div class="spec-row"><span class="spec-label">Series Title:</span><span class="spec-value">${escapeHtml(wizTitle.value || 'Untitled')}</span></div>
        <div class="spec-row"><span class="spec-label">Niche:</span><span class="spec-value">${escapeHtml(wizNiche.value)}</span></div>
        <div class="spec-row"><span class="spec-label">Focus Theme:</span><span class="spec-value">${escapeHtml(wizKeyword.value || 'None')}</span></div>
        <div class="spec-row"><span class="spec-label">Audience:</span><span class="spec-value">${escapeHtml(wizSelectedDemographic)}</span></div>
        <div class="spec-row"><span class="spec-label">Visual Style:</span><span class="spec-value">${escapeHtml(wizSelectedStyle)}</span></div>
        <div class="spec-row"><span class="spec-label">Narrator:</span><span class="spec-value">${escapeHtml(wizVoiceTone.value)}</span></div>
        <div class="spec-row"><span class="spec-label">Duration:</span><span class="spec-value">${wizRangeDuration.value}s</span></div>
      `;
    }
  }

  wizBtnPrev.addEventListener('click', () => {
    if (activeWizardStep > 1) {
      activeWizardStep--;
      updateWizardUI();
    }
  });

  wizBtnNext.addEventListener('click', async () => {
    if (activeWizardStep < 5) {
      activeWizardStep++;
      updateWizardUI();
    } else {
      // Launch from wizard
      wizBtnNext.disabled = true;
      wizBtnNext.textContent = 'Launching...';

      const payload = {
        title: wizTitle.value.trim() || "Untitled Project",
        niche: wizNiche.value,
        focus_keyword: wizKeyword.value.trim() || null,
        visual_style: wizSelectedStyle,
        target_duration_sec: parseInt(wizRangeDuration.value, 10),
        target_demographic: wizSelectedDemographic,
        voice_tone: wizVoiceTone.value,
        recap_intro: document.getElementById('wiz-recap').value.trim() || null,
        custom_cliffhanger: document.getElementById('wiz-cliffhanger').value.trim() || null
      };

      try {
        const resp = await fetch('/api/jobs', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (!resp.ok) throw new Error('Submission failed');
        const job = await resp.json();
        closeWizard();
        showToast('Production dispatched from wizard!', 'success');

        const jobsTabBtn = document.querySelector('[data-tab="tab-jobs"]');
        jobsTabBtn.click();
        fetchJobs();
        openDrawer(job.id);
      } catch (err) {
        showToast(err.message, 'error');
      } finally {
        wizBtnNext.disabled = false;
        wizBtnNext.textContent = '🚀 Launch Production';
      }
    }
  });

  // =========================================================================
  // 9. Diagnostics & Models Tab
  // =========================================================================

  async function fetchDiagnostics() {
    const healthContainer = document.getElementById('health-checks-list');
    const modelsContainer = document.getElementById('models-list-container');

    try {
      const resp = await fetch('/api/health');
      const data = await resp.json();

      healthContainer.innerHTML = `
        <div class="spec-row"><span class="spec-label">Server Status:</span><span class="spec-value text-success">${data.status}</span></div>
        <div class="spec-row"><span class="spec-label">fal.ai API Key Configured:</span><span class="spec-value">${data.api_key_configured ? '✅ Yes' : '⚠️ Missing (Fallback Active)'}</span></div>
        <div class="spec-row"><span class="spec-label">High-Quality Fallback Engine:</span><span class="spec-value">${data.fallback_mode_enabled ? '✅ Active' : '❌ Disabled'}</span></div>
        <div class="spec-row"><span class="spec-label">SQLite Database:</span><span class="spec-value">Connected (${data.database_path})</span></div>
      `;

      const modelsResp = await fetch('/api/models');
      const modelsData = await modelsResp.json();

      modelsContainer.innerHTML = modelsData.models.map(m => `
        <div class="glass-panel" style="padding: 14px; border-radius: var(--radius-sm); margin-bottom: 10px;">
          <strong>${escapeHtml(m.name)}</strong><br>
          <span style="font-family: var(--font-mono); font-size: 0.75rem; color: var(--accent-primary);">${m.id}</span>
          <p style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 4px;">${escapeHtml(m.description)}</p>
        </div>
      `).join('');
    } catch (e) {
      console.error("Diagnostics load failed:", e);
    }
  }

  // =========================================================================
  // 10. Utilities (Toasts & Sanitization)
  // =========================================================================

  function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
      toast.remove();
    }, 4000);
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/[&<>"']/g, s => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;'
    }[s]));
  }

  // Initial jobs load
  fetchJobs();
});
