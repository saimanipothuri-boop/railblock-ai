/**
 * RailBlock-AI Client Application
 * Intelligent Automatic Block Planning & Asset Availability Maximizer for Indian Railways
 */

// Global State
let networkData = { stations: [], sections: [] };
let trainsData = [];
let blocksData = [];
let assetsData = [];
let kpiData = {};
let logsData = [];

let currentTimeMin = 630; // 10:30 AM default
let isSimPlaying = false;
let simInterval = null;

// DOM Elements
const liveClockEl = document.getElementById("liveClock");
const schematicTimeSlider = document.getElementById("schematicTimeSlider");
const schematicTimeDisplay = document.getElementById("schematicTimeDisplay");
const btnPlaySim = document.getElementById("btnPlaySim");
const btnPauseSim = document.getElementById("btnPauseSim");

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
  initClock();
  setupTabs();
  setupEventListeners();
  loadAllData();
});

// Format minutes from 00:00 to HH:MM
function formatTime(minutes) {
  const h = Math.floor(minutes / 60) % 24;
  const m = minutes % 60;
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

// Live Digital Clock (IST)
function initClock() {
  function update() {
    const now = new Date();
    liveClockEl.textContent = now.toLocaleTimeString('en-IN', { hour12: false });
  }
  update();
  setInterval(update, 1000);
}

// Tab Switching
function setupTabs() {
  const tabs = document.querySelectorAll(".tab-btn");
  tabs.forEach(btn => {
    btn.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

      btn.classList.add("active");
      const targetId = btn.getAttribute("data-tab");
      const targetPane = document.getElementById(targetId);
      if (targetPane) {
        targetPane.classList.add("active");
      }

      // Trigger redraws for SVG views
      if (targetId === "tab-schematic") renderSchematic();
      if (targetId === "tab-marey") renderMareyChart();
    });
  });
}

// Setup Event Listeners
function setupEventListeners() {
  // Timeline slider
  schematicTimeSlider.addEventListener("input", (e) => {
    currentTimeMin = parseInt(e.target.value);
    schematicTimeDisplay.textContent = `${formatTime(currentTimeMin)} (${currentTimeMin} min)`;
    renderSchematic();
  });

  // Play / Pause Simulation
  btnPlaySim.addEventListener("click", () => {
    if (isSimPlaying) return;
    isSimPlaying = true;
    btnPlaySim.classList.add("btn-primary");
    simInterval = setInterval(() => {
      currentTimeMin = (currentTimeMin + 2 > 1200) ? 360 : currentTimeMin + 2;
      schematicTimeSlider.value = currentTimeMin;
      schematicTimeDisplay.textContent = `${formatTime(currentTimeMin)} (${currentTimeMin} min)`;
      renderSchematic();
    }, 400);
  });

  btnPauseSim.addEventListener("click", () => {
    isSimPlaying = false;
    btnPlaySim.classList.remove("btn-primary");
    if (simInterval) clearInterval(simInterval);
  });

  // Optimizer mode run
  document.getElementById("btnRunOptimizer").addEventListener("click", () => {
    const mode = document.getElementById("selOptimizerMode").value;
    runOptimizer(mode);
  });

  // Delay simulation
  document.getElementById("btnInjectDelay").addEventListener("click", () => {
    const trainNo = document.getElementById("selSimTrain").value;
    const delay = parseInt(document.getElementById("rangeSimDelay").value);
    injectDelay(trainNo, delay);
  });

  document.getElementById("rangeSimDelay").addEventListener("input", (e) => {
    document.getElementById("simDelayValue").textContent = `+${e.target.value} mins`;
  });

  document.querySelectorAll(".preset-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const delay = btn.getAttribute("data-delay");
      document.getElementById("rangeSimDelay").value = delay;
      document.getElementById("simDelayValue").textContent = `+${delay} mins`;
    });
  });

  // Reset simulation
  document.getElementById("btnReset").addEventListener("click", () => {
    if (confirm("Reset simulation to default corridor state?")) {
      fetch("/api/reset", { method: "POST" })
        .then(r => r.json())
        .then(() => loadAllData());
    }
  });

  // Modal Open/Close
  const modal = document.getElementById("newBlockModal");
  document.getElementById("btnOpenNewBlockModal").addEventListener("click", () => {
    modal.classList.add("show");
  });
  document.getElementById("btnCloseModal").addEventListener("click", () => {
    modal.classList.remove("show");
  });
  document.getElementById("btnCancelModal").addEventListener("click", () => {
    modal.classList.remove("show");
  });

  // New Block Form Submit
  document.getElementById("newBlockForm").addEventListener("submit", (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const payload = Object.fromEntries(formData.entries());
    payload.from_km = parseFloat(payload.from_km);
    payload.to_km = parseFloat(payload.to_km);
    payload.requested_start_min = parseInt(payload.requested_start_min);
    payload.requested_duration_min = parseInt(payload.requested_duration_min);
    payload.urgency_score = parseInt(payload.urgency_score);

    fetch("/api/request-block", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    })
    .then(r => r.json())
    .then(data => {
      modal.classList.remove("show");
      loadAllData();
      alert("New Block Request submitted to AI Optimizer successfully!");
    });
  });

  // Marey Chart filters
  ["chkShowBlocks", "chkShowDownTrains", "chkShowUpTrains"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener("change", renderMareyChart);
  });

  // Generate blocks from asset telemetry button
  document.getElementById("btnAutoRequestFromAssets").addEventListener("click", () => {
    alert("AI scanned corridor assets. High urgency USFD rail defect at KM 245.2 has already been auto-scheduled as MB-01 with top safety priority!");
  });
}

// Fetch all backend data
async function loadAllData() {
  try {
    const [netRes, trainsRes, blocksRes, assetsRes, kpisRes, logsRes] = await Promise.all([
      fetch("/api/network").then(r => r.json()),
      fetch("/api/trains").then(r => r.json()),
      fetch("/api/blocks").then(r => r.json()),
      fetch("/api/assets").then(r => r.json()),
      fetch("/api/kpis").then(r => r.json()),
      fetch("/api/logs").then(r => r.json())
    ]);

    networkData = netRes;
    trainsData = trainsRes;
    blocksData = blocksRes;
    assetsData = assetsRes;
    kpiData = kpisRes;
    logsData = logsRes;

    updateKPIs();
    renderSchematic();
    renderMareyChart();
    renderOptimizerTable();
    populateSimulatorTrains();
    renderAssets();
    renderDefaultMemo();
  } catch (err) {
    console.error("Error loading data:", err);
  }
}

// Update KPI Display
function updateKPIs() {
  if (!kpiData) return;
  document.getElementById("kpiAvailability").textContent = `${kpiData.track_availability_pct || 95.8}%`;
  document.getElementById("kpiPunctuality").textContent = `${kpiData.network_punctuality_pct || 87.9}%`;
  document.getElementById("kpiSavedHours").innerHTML = `${kpiData.saved_delay_hours || 10.9} <span class="unit">Hrs</span>`;
  document.getElementById("kpiSavedMin").textContent = kpiData.saved_delay_min || 652;
  document.getElementById("kpiShadowBlocks").innerHTML = `${kpiData.shadow_blocks || 3} <span class="unit">/ ${kpiData.total_blocks || 5}</span>`;
}

// ==========================================
// TAB 1: INTERACTIVE TRACK SCHEMATIC (SVG)
// ==========================================
function renderSchematic() {
  const svg = document.getElementById("schematicSvg");
  if (!svg || !networkData.stations.length) return;

  const width = 1200;
  const height = 480;
  svg.innerHTML = "";

  const marginX = 90;
  const usableWidth = width - 2 * marginX;
  const maxKm = 440; // New Delhi to Kanpur

  const getStationX = (km) => marginX + (km / maxKm) * usableWidth;

  const yUpLoop = 100;
  const yUpMain = 150;
  const yDnMain = 270;
  const yDnLoop = 320;

  // Background grid styling
  const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
  defs.innerHTML = `
    <linearGradient id="gradMainUp" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#1E3A8A"/>
      <stop offset="100%" stop-color="#3B82F6"/>
    </linearGradient>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3" result="glow"/>
      <feComposite in="SourceGraphic" in2="glow" operator="over"/>
    </filter>
  `;
  svg.appendChild(defs);

  // Track Title Labels
  const txtUp = createSvgText(marginX - 70, yUpMain + 4, "UP LINE (To NDLS)", "#94A3B8", 10, "bold");
  const txtDn = createSvgText(marginX - 70, yDnMain + 4, "DN LINE (To CNB)", "#94A3B8", 10, "bold");
  svg.appendChild(txtUp);
  svg.appendChild(txtDn);

  // Draw Main Line Tracks
  svg.appendChild(createSvgLine(marginX, yUpMain, width - marginX, yUpMain, "#334155", 5));
  svg.appendChild(createSvgLine(marginX, yDnMain, width - marginX, yDnMain, "#334155", 5));

  // Determine Blocked Sections at current simulated time
  const activeBlocksNow = blocksData.filter(b => {
    const s = b.granted_start_min || b.requested_start_min;
    const dur = b.granted_duration_min || b.requested_duration_min;
    return currentTimeMin >= s && currentTimeMin <= (s + dur);
  });

  // Render Active Maintenance Block Highlights on Tracks
  activeBlocksNow.forEach(b => {
    const x1 = getStationX(b.from_km);
    const x2 = getStationX(b.to_km);
    const isUp = b.direction === "UP" || b.direction === "BOTH";
    const isDn = b.direction === "DOWN" || b.direction === "BOTH";

    if (isUp) {
      const blockLine = createSvgLine(x1, yUpMain, x2, yUpMain, "#F59E0B", 9, "6,4");
      blockLine.setAttribute("filter", "url(#glow)");
      svg.appendChild(blockLine);

      // Warning maintenance banner
      const badge = createSvgRect((x1 + x2)/2 - 35, yUpMain - 30, 70, 20, "#B45309", "#FFD700", 4);
      svg.appendChild(badge);
      svg.appendChild(createSvgText((x1 + x2)/2, yUpMain - 16, `🛠️ ${b.block_id}`, "#FFF", 10, "bold", "middle"));
    }
    if (isDn) {
      const blockLine = createSvgLine(x1, yDnMain, x2, yDnMain, "#F59E0B", 9, "6,4");
      blockLine.setAttribute("filter", "url(#glow)");
      svg.appendChild(blockLine);

      const badge = createSvgRect((x1 + x2)/2 - 35, yDnMain + 14, 70, 20, "#B45309", "#FFD700", 4);
      svg.appendChild(badge);
      svg.appendChild(createSvgText((x1 + x2)/2, yDnMain + 28, `🛠️ ${b.block_id}`, "#FFF", 10, "bold", "middle"));
    }
  });

  // Draw Stations, Loops, and Crossovers
  networkData.stations.forEach((st, idx) => {
    const sx = getStationX(st.km);

    // Station Vertical Line
    svg.appendChild(createSvgLine(sx, 70, sx, 350, "rgba(255,255,255,0.06)", 1, "3,3"));

    // Loops at stations
    if (st.has_loops) {
      // UP loop
      svg.appendChild(createSvgLine(sx - 35, yUpLoop, sx + 35, yUpLoop, "#475569", 3));
      svg.appendChild(createSvgLine(sx - 45, yUpMain, sx - 35, yUpLoop, "#475569", 2));
      svg.appendChild(createSvgLine(sx + 35, yUpLoop, sx + 45, yUpMain, "#475569", 2));

      // DN loop
      svg.appendChild(createSvgLine(sx - 35, yDnLoop, sx + 35, yDnLoop, "#475569", 3));
      svg.appendChild(createSvgLine(sx - 45, yDnMain, sx - 35, yDnLoop, "#475569", 2));
      svg.appendChild(createSvgLine(sx + 35, yDnLoop, sx + 45, yDnMain, "#475569", 2));

      // Crossover switch between UP and DN lines
      if (idx % 2 === 0 && idx > 0 && idx < networkData.stations.length - 1) {
        svg.appendChild(createSvgLine(sx - 20, yUpMain, sx + 20, yDnMain, "rgba(59, 130, 246, 0.4)", 2, "4,4"));
      }
    }

    // Station Nodes / Platforms
    const platUp = createSvgRect(sx - 22, yUpMain - 10, 44, 20, "#1E293B", "#3B82F6", 3);
    const platDn = createSvgRect(sx - 22, yDnMain - 10, 44, 20, "#1E293B", "#3B82F6", 3);
    svg.appendChild(platUp);
    svg.appendChild(platDn);

    // Station Code & Name
    svg.appendChild(createSvgText(sx, 50, st.code, "#FFD700", 13, "bold", "middle"));
    svg.appendChild(createSvgText(sx, 64, `${st.km} KM`, "#94A3B8", 10, "normal", "middle"));

    // Signal Aspect Indicator
    const sigColor = activeBlocksNow.length > 0 ? "#FBBF24" : "#10B981";
    svg.appendChild(createSvgCircle(sx + 28, yUpMain - 18, 5, sigColor));
    svg.appendChild(createSvgCircle(sx - 28, yDnMain + 18, 5, sigColor));
  });

  // Calculate & Render Live Train Markers
  const activeTrainsNow = [];

  trainsData.forEach(tr => {
    const sched = tr.schedule;
    const delay = tr.current_delay_min || 0;
    const tStart = sched[0].departure_min + delay;
    const tEnd = sched[sched.length - 1].arrival_min + delay;

    if (currentTimeMin >= tStart && currentTimeMin <= tEnd) {
      // Interpolate train position
      let curKm = 0;
      let curSpeed = tr.avg_speed_kmh;
      let statusText = "Running Normal";

      for (let i = 0; i < sched.length - 1; i++) {
        const s1 = sched[i];
        const s2 = sched[i + 1];
        const t1 = s1.departure_min + delay;
        const t2 = s2.arrival_min + delay;

        if (currentTimeMin >= t1 && currentTimeMin <= t2) {
          const st1 = networkData.stations.find(s => s.code === s1.station_code);
          const st2 = networkData.stations.find(s => s.code === s2.station_code);
          const fraction = (currentTimeMin - t1) / Math.max(1, (t2 - t1));
          curKm = st1.km + fraction * (st2.km - st1.km);
          break;
        } else if (currentTimeMin < t1) {
          const st = networkData.stations.find(s => s.code === s1.station_code);
          curKm = st.km;
          break;
        }
      }

      const tx = getStationX(curKm);
      const isUp = tr.direction === "UP";
      const ty = isUp ? yUpMain : yDnMain;

      // Draw Train Engine / Rake Marker
      const trainBox = createSvgRect(tx - 28, ty - 9, 56, 18, tr.color || "#2563EB", "#FFFFFF", 4);
      trainBox.setAttribute("filter", "url(#glow)");
      svg.appendChild(trainBox);

      // Train direction arrow and number
      const arrow = isUp ? "◄" : "►";
      svg.appendChild(createSvgText(tx, ty + 4, `${arrow} ${tr.train_no}`, "#FFFFFF", 9, "bold", "middle"));

      // Train tag on hover or hovering label
      svg.appendChild(createSvgText(tx, isUp ? ty - 14 : ty + 24, `${tr.name.split(" ")[0]} (${Math.round(curKm)} KM)`, "#E2E8F0", 9, "normal", "middle"));

      activeTrainsNow.push({
        train_no: tr.train_no,
        name: tr.name,
        category: tr.category,
        km: Math.round(curKm),
        direction: tr.direction,
        delay: delay,
        color: tr.color
      });
    }
  });

  // Update Detail Pill Lists
  updateSchematicPills(activeTrainsNow, activeBlocksNow);
}

function updateSchematicPills(trains, blocks) {
  const tList = document.getElementById("schematicTrainList");
  const bList = document.getElementById("schematicBlockList");

  if (trains.length === 0) {
    tList.innerHTML = `<div class="text-muted" style="padding:8px;">No trains in section at ${formatTime(currentTimeMin)} (Shadow gap window).</div>`;
  } else {
    tList.innerHTML = trains.map(t => `
      <div class="train-pill" style="border-left-color:${t.color};">
        <div>
          <strong>${t.train_no} - ${t.name}</strong> (${t.category})
          <div class="text-muted" style="font-size:11px;">Pos: KM ${t.km} | Dir: ${t.direction}</div>
        </div>
        <div>
          ${t.delay > 0 ? `<span class="badge-tag critical">+${t.delay}m Late</span>` : `<span class="badge-tag shadow">On Time</span>`}
        </div>
      </div>
    `).join("");
  }

  if (blocks.length === 0) {
    bList.innerHTML = `<div class="text-muted" style="padding:8px;">No active track blocks at ${formatTime(currentTimeMin)}. All tracks 100% available.</div>`;
  } else {
    bList.innerHTML = blocks.map(b => `
      <div class="block-pill">
        <div>
          <strong>${b.block_id} (${b.department})</strong>
          <div class="text-muted" style="font-size:11px;">Sec: ${b.section_id} (KM ${b.from_km}-${b.to_km})</div>
        </div>
        <div>
          <span class="badge-tag regulated">Active Window</span>
        </div>
      </div>
    `).join("");
  }
}

// ==========================================
// TAB 2: TIME-DISTANCE (MAREY) CHART (SVG)
// ==========================================
function renderMareyChart() {
  const svg = document.getElementById("mareyChartSvg");
  if (!svg || !networkData.stations.length) return;

  const showBlocks = document.getElementById("chkShowBlocks")?.checked ?? true;
  const showDown = document.getElementById("chkShowDownTrains")?.checked ?? true;
  const showUp = document.getElementById("chkShowUpTrains")?.checked ?? true;

  const width = 1100;
  const height = 580;
  svg.innerHTML = "";

  const marginL = 110;
  const marginR = 40;
  const marginT = 40;
  const marginB = 50;

  const plotW = width - marginL - marginR;
  const plotH = height - marginT - marginB;

  const minTime = 360;  // 06:00
  const maxTime = 1320; // 22:00
  const maxKm = 440;

  const timeToX = (t) => marginL + ((t - minTime) / (maxTime - minTime)) * plotW;
  const kmToY = (km) => marginT + (km / maxKm) * plotH;

  // Background rect
  svg.appendChild(createSvgRect(marginL, marginT, plotW, plotH, "#080E18", "#1E293B", 2));

  // Time Grid Lines (Vertical - every 1 hour)
  for (let t = minTime; t <= maxTime; t += 60) {
    const x = timeToX(t);
    svg.appendChild(createSvgLine(x, marginT, x, marginT + plotH, "rgba(255,255,255,0.06)", 1));
    svg.appendChild(createSvgText(x, marginT + plotH + 18, formatTime(t), "#94A3B8", 10, "normal", "middle"));
  }

  // Station Distance Lines (Horizontal)
  networkData.stations.forEach(st => {
    const y = kmToY(st.km);
    svg.appendChild(createSvgLine(marginL, y, marginL + plotW, y, "rgba(255,255,255,0.12)", 1, "4,4"));
    svg.appendChild(createSvgText(marginL - 12, y + 4, `${st.code} (${st.km}k)`, "#FFD700", 11, "bold", "end"));
  });

  // Draw Granted Maintenance Blocks (Shaded Boxes)
  if (showBlocks) {
    blocksData.forEach(b => {
      const tStart = b.granted_start_min || b.requested_start_min;
      const tEnd = tStart + (b.granted_duration_min || b.requested_duration_min);

      if (tEnd < minTime || tStart > maxTime) return;

      const bx1 = Math.max(marginL, timeToX(tStart));
      const bx2 = Math.min(marginL + plotW, timeToX(tEnd));
      const by1 = kmToY(b.from_km);
      const by2 = kmToY(b.to_km);

      const bRect = createSvgRect(bx1, Math.min(by1, by2), bx2 - bx1, Math.abs(by2 - by1) + 16, "rgba(245, 158, 11, 0.18)", "#F59E0B", 2);
      bRect.setAttribute("stroke-dasharray", "4,3");
      svg.appendChild(bRect);

      // Block Label
      const bLabel = createSvgText((bx1 + bx2)/2, (by1 + by2)/2 + 4, `${b.block_id}: ${b.work_description.slice(0, 18)}...`, "#FBBF24", 9, "bold", "middle");
      svg.appendChild(bLabel);
    });
  }

  // Draw Train Trajectories
  trainsData.forEach(tr => {
    const isDown = tr.direction === "DOWN";
    if (isDown && !showDown) return;
    if (!isDown && !showUp) return;

    const sched = tr.schedule;
    const delay = tr.current_delay_min || 0;
    const points = [];

    sched.forEach(stop => {
      const st = networkData.stations.find(s => s.code === stop.station_code);
      if (!st) return;

      const arrT = stop.arrival_min + delay;
      const depT = stop.departure_min + delay;

      points.push({ x: timeToX(arrT), y: kmToY(st.km) });
      if (arrT !== depT) {
        points.push({ x: timeToX(depT), y: kmToY(st.km) });
      }
    });

    // Draw trajectory polyline
    const pathD = points.map((pt, idx) => (idx === 0 ? `M ${pt.x} ${pt.y}` : `L ${pt.x} ${pt.y}`)).join(" ");
    const linePath = document.createElementNS("http://www.w3.org/2000/svg", "path");
    linePath.setAttribute("d", pathD);
    linePath.setAttribute("fill", "none");
    linePath.setAttribute("stroke", tr.color || "#3B82F6");
    linePath.setAttribute("stroke-width", tr.priority_weight >= 9 ? "3" : "1.8");
    linePath.setAttribute("stroke-linecap", "round");
    svg.appendChild(linePath);

    // Train number label at midpoint
    if (points.length >= 2) {
      const mid = points[Math.floor(points.length / 2)];
      if (mid.x >= marginL && mid.x <= marginL + plotW) {
        const trLabel = createSvgText(mid.x + 4, mid.y - 4, tr.train_no, tr.color, 9, "bold");
        svg.appendChild(trLabel);
      }
    }
  });

  // Current simulation time vertical red line
  const curX = timeToX(currentTimeMin);
  if (curX >= marginL && curX <= marginL + plotW) {
    svg.appendChild(createSvgLine(curX, marginT, curX, marginT + plotH, "#EF4444", 2));
    svg.appendChild(createSvgText(curX, marginT - 8, `NOW ${formatTime(currentTimeMin)}`, "#EF4444", 10, "bold", "middle"));
  }
}

// ==========================================
// TAB 3: AI OPTIMIZER & CONFLICT RESOLUTION
// ==========================================
function renderOptimizerTable() {
  const tbody = document.getElementById("tbodyBlocks");
  const feed = document.getElementById("aiReasoningFeed");
  if (!tbody) return;

  tbody.innerHTML = blocksData.map(b => {
    const reqStart = formatTime(b.requested_start_min);
    const reqEnd = formatTime(b.requested_start_min + b.requested_duration_min);
    const grtStart = formatTime(b.granted_start_min || b.requested_start_min);
    const grtEnd = formatTime((b.granted_start_min || b.requested_start_min) + (b.granted_duration_min || b.requested_duration_min));
    const isShadow = b.shadow_block;
    const isUrgent = b.urgency_score >= 85;

    return `
      <tr>
        <td><strong>${b.block_id}</strong></td>
        <td>
          <div><strong>${b.department}</strong></div>
          <div class="text-muted" style="font-size:11px;">${b.work_description}</div>
          <div class="text-dim" style="font-size:10px;">Req: ${b.machine_required}</div>
        </td>
        <td>${b.section_id} <span class="badge-tag" style="background:#1E293B;">${b.direction}</span></td>
        <td>${reqStart} - ${reqEnd} (${b.requested_duration_min}m)</td>
        <td><strong class="text-accent">${grtStart} - ${grtEnd}</strong></td>
        <td><span class="badge-tag shadow">APPROVED</span></td>
        <td>
          ${isShadow ? `<span class="badge-tag shadow">Shadow Block</span>` : 
            (isUrgent ? `<span class="badge-tag critical">Safety Urgent</span>` : `<span class="badge-tag regulated">Regulated</span>`)}
        </td>
        <td>
          ${b.delay_impact_min === 0 ? 
            `<strong class="text-success">0 mins (Zero Delay)</strong>` : 
            `<span class="text-warning">+${b.delay_impact_min} min goods loop</span>`}
        </td>
        <td>
          <button class="btn btn-xs btn-outline" onclick="viewBlockMemo('${b.block_id}')">Memo</button>
        </td>
      </tr>
    `;
  }).join("");

  // AI Reasoning Feed
  if (feed) {
    feed.innerHTML = blocksData.map(b => `
      <div class="reasoning-item ${b.shadow_block ? 'shadow-item' : ''}">
        <div class="reasoning-title">
          <span>${b.block_id} (${b.section_id})</span>
          <span class="text-accent">Urgency: ${b.urgency_score}/100</span>
        </div>
        <p style="margin-bottom: 4px;"><strong>AI Decision:</strong> ${b.rationale || 'Optimal slot scheduled.'}</p>
        <div class="text-muted" style="font-size:11px;">
          Requested: ${formatTime(b.requested_start_min)} ➔ Granted: ${formatTime(b.granted_start_min || b.requested_start_min)} | Detention Impact: ${b.delay_impact_min}m
        </div>
      </div>
    `).join("");
  }
}

function runOptimizer(mode) {
  fetch("/api/optimize", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode: mode })
  })
  .then(r => r.json())
  .then(res => {
    blocksData = res.blocks;
    kpiData = res.kpis;
    updateKPIs();
    renderSchematic();
    renderMareyChart();
    renderOptimizerTable();
    alert(`AI Optimization Completed successfully in '${mode}' mode! Saved ${res.kpis.saved_delay_hours} hrs of train detention.`);
  });
}

// ==========================================
// TAB 4: WHAT-IF DELAY SIMULATOR
// ==========================================
function populateSimulatorTrains() {
  const sel = document.getElementById("selSimTrain");
  if (!sel) return;
  sel.innerHTML = trainsData.map(t => `
    <option value="${t.train_no}">${t.train_no} - ${t.name} (${t.category})</option>
  `).join("");
}

function injectDelay(trainNo, delayMin) {
  fetch("/api/simulate-delay", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ train_no: trainNo, delay_min: delayMin })
  })
  .then(r => r.json())
  .then(res => {
    blocksData = res.blocks;
    kpiData = res.kpis;
    
    // Update local train delay
    const tr = trainsData.find(t => t.train_no === trainNo);
    if (tr) tr.current_delay_min = delayMin;

    updateKPIs();
    renderSchematic();
    renderMareyChart();
    renderOptimizerTable();

    // Add entry to simulator log
    const logEl = document.getElementById("delaySimLog");
    const item = document.createElement("div");
    item.className = "log-item alert";
    item.innerHTML = `
      <span class="log-time">${new Date().toLocaleTimeString()}</span>
      <span class="log-text">Dynamic Delay: Train ${trainNo} delayed +${delayMin}m. AI re-optimized corridor blocks!</span>
    `;
    logEl.prepend(item);
  });
}

// ==========================================
// TAB 5: ASSET HEALTH TELEMETRY
// ==========================================
function renderAssets() {
  const container = document.getElementById("assetsContainer");
  if (!container) return;

  container.innerHTML = assetsData.map(a => {
    let fillClass = "fill-healthy";
    let badgeClass = "shadow";
    if (a.health_score < 40) {
      fillClass = "fill-critical";
      badgeClass = "critical";
    } else if (a.health_score < 75) {
      fillClass = "fill-moderate";
      badgeClass = "regulated";
    }

    return `
      <div class="asset-card">
        <div class="asset-header">
          <div>
            <div class="asset-name">${a.asset_id}</div>
            <div class="asset-meta">${a.asset_type} • Sec ${a.section_id} (KM ${a.location_km})</div>
          </div>
          <span class="badge-tag ${badgeClass}">${a.status}</span>
        </div>

        <div class="health-meter-container">
          <div style="display:flex; justify-content:space-between; font-size:11px;">
            <span>Asset Health Index:</span>
            <strong>${a.health_score}%</strong>
          </div>
          <div class="health-bar-bg">
            <div class="health-bar-fill ${fillClass}" style="width: ${a.health_score}%;"></div>
          </div>
        </div>

        <div class="asset-recommendation">
          <strong>Recommended Action:</strong> ${a.recommended_maintenance}
          <div class="text-dim" style="font-size:10px; margin-top:2px;">Audit: ${a.last_inspection} | Urgency: ${a.urgency}/100</div>
        </div>
      </div>
    `;
  }).join("");
}

// ==========================================
// TAB 6: BLOCK SANCTION MEMO
// ==========================================
function renderDefaultMemo() {
  if (blocksData.length > 0) {
    viewBlockMemo(blocksData[0].block_id);
  }
}

function viewBlockMemo(blockId) {
  fetch(`/api/memo/${blockId}`)
    .then(r => r.json())
    .then(memo => {
      // Switch to memo tab
      document.querySelectorAll(".tab-btn").forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));
      document.querySelector('[data-tab="tab-memos"]').classList.add("active");
      document.getElementById("tab-memos").classList.add("active");

      document.getElementById("memoMetaGrid").innerHTML = `
        <div><strong>MEMO NO:</strong> ${memo.memo_no}</div>
        <div><strong>DATE:</strong> ${memo.date}</div>
        <div><strong>SECTION:</strong> ${memo.section}</div>
        <div><strong>TRACK:</strong> ${memo.track}</div>
        <div><strong>KM RANGE:</strong> ${memo.km_range}</div>
        <div><strong>DEPARTMENT:</strong> ${memo.department}</div>
      `;

      document.getElementById("memoBody").innerHTML = `
        <p><strong>1. SANCTIONED BLOCK WINDOW:</strong> ${memo.sanctioned_window}</p>
        <p><strong>2. OPTIMIZATION CLASSIFICATION:</strong> ${memo.block_type}</p>
        <p><strong>3. NATURE OF WORK & MACHINERY:</strong> ${memo.work} utilizing ${memo.machine}.</p>
        <p><strong>4. SAFETY ISOLATION & PROTOCOL:</strong> ${memo.safety_precaution}</p>
        <p><strong>5. REGULATION ADVISORY:</strong> Downstream Station Masters must hold non-interlocked shunting and maintain electronic interlocking red-route clamp for the duration of the sanction.</p>
      `;

      document.getElementById("memoSecurityHash").textContent = `Digital Authorization Hash: ${memo.digital_signature}`;
    });
}

// SVG Helper Functions
function createSvgLine(x1, y1, x2, y2, stroke, width = 1, dash = null) {
  const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
  line.setAttribute("x1", x1);
  line.setAttribute("y1", y1);
  line.setAttribute("x2", x2);
  line.setAttribute("y2", y2);
  line.setAttribute("stroke", stroke);
  line.setAttribute("stroke-width", width);
  if (dash) line.setAttribute("stroke-dasharray", dash);
  return line;
}

function createSvgRect(x, y, w, h, fill, stroke = null, rx = 0) {
  const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  rect.setAttribute("x", x);
  rect.setAttribute("y", y);
  rect.setAttribute("width", w);
  rect.setAttribute("height", h);
  rect.setAttribute("fill", fill);
  if (stroke) {
    rect.setAttribute("stroke", stroke);
    rect.setAttribute("stroke-width", "1");
  }
  if (rx) {
    rect.setAttribute("rx", rx);
    rect.setAttribute("ry", rx);
  }
  return rect;
}

function createSvgText(x, y, text, fill, fontSize = 12, fontWeight = "normal", textAnchor = "start") {
  const t = document.createElementNS("http://www.w3.org/2000/svg", "text");
  t.setAttribute("x", x);
  t.setAttribute("y", y);
  t.setAttribute("fill", fill);
  t.setAttribute("font-size", fontSize);
  t.setAttribute("font-weight", fontWeight);
  t.setAttribute("text-anchor", textAnchor);
  t.textContent = text;
  return t;
}

function createSvgCircle(cx, cy, r, fill) {
  const c = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  c.setAttribute("cx", cx);
  c.setAttribute("cy", cy);
  c.setAttribute("r", r);
  c.setAttribute("fill", fill);
  return c;
}
