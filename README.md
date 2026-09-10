# RailBlock-AI: AI-Powered Automatic Block Planning System
### Smart India Hackathon (SIH) | Ministry of Railways Prototype

An intelligent decision-support system that automatically schedules railway track maintenance windows ("blocks") to **maximize track asset availability** while protecting **train punctuality** across high-density corridors.

---

## 🌟 Core Features

1. **AI Multi-Objective Constraint Solver (`optimizer.py`)**:
   - **Shadow Block Discovery**: Scans train timetables to find natural headway gaps (90–180 mins) between train bunches, scheduling maintenance with **0 minutes of train detention**.
   - **Precedence & Priority Rules**: Strict protection for premium passenger trains (*Vande Bharat*, *Rajdhani Express*, *Shatabdi*) while intelligently regulating freight on station loop lines.
   - **Urgency Weighting**: Automatically prioritizes safety-critical assets (e.g. Ultrasonic Flaw Detection / USFD rail weld defects) to eliminate rail fracture risks.

2. **Section Controller Live Track Schematic**:
   - High-Density Trunk Route (HDN-1: New Delhi – Kanpur Central, 440 km).
   - Dual track lines (UP & DOWN), loop lines, crossovers, and 3-aspect automatic block signaling.
   - Real-time animated train movements and visual maintenance isolation zones.
   - Interactive timeline slider (06:00 to 20:00) with Play/Pause simulation.

3. **Time-Distance (Marey) Diagram**:
   - The hallmark 24-hour graphical timetable used by Indian Railways section controllers.
   - Slanted train trajectory lines mapped against distance (KM 0 to 440).
   - Shaded maintenance blocks showing exactly how trains clear or bypass track closures.

4. **"What-If" Dynamic Delay Simulator**:
   - Inject unexpected delays into any train (e.g., *Rajdhani running 35 mins late*).
   - Watch the AI dynamically shift downstream maintenance windows in real time to avoid cascading gridlock.

5. **Corridor Asset Health Telemetry**:
   - Tracks Track Quality Index (TQI), USFD rail weld flaws, OHE contact wire wear (mm), and Point Machine operating currents.

6. **Official Block Sanction Memo Dispatcher**:
   - Generates the standard Indian Railways Joint Block Sanction Memo between Section Controller (DOM), P-Way Engineer, and Station Masters, complete with digital verification hashes.

---

## 🚀 Quick Start Instructions

The web server is lightweight and requires **zero external dependencies** (built with Python standard library):

```bash
# Navigate to the project directory
cd "c:\Users\saima\OneDrive\Documents\SIH HACKTHON"

# Start the server
python server.py
```

Open your web browser and visit:
👉 **[http://localhost:8000](http://localhost:8000)**

---

## 📁 Project Architecture

```
SIH HACKTHON/
├── models.py          # Data models (Train, Section, MaintenanceBlock, AssetHealth)
├── data.py            # Corridor dataset (HDN-1 New Delhi - Kanpur, 16 trains, 5 blocks)
├── optimizer.py       # AI Optimization Engine (Constraint solver, shadow gap finder)
├── server.py          # REST API & Web Server (HTTP server on port 8000)
├── test_system.py     # Automated test suite
├── public/
│   ├── index.html     # Indian Railways Command Center UI
│   ├── style.css      # Dark-mode dashboard stylesheet
│   └── app.js         # Interactive SVG schematic, Marey chart, and client logic
└── README.md          # Project documentation
```

---

## 📊 Demonstrated Impact (Baseline Results)

- **Track Asset Availability:** **95.83%**
- **Train Detention Saved:** **10.9 Hours** (652 mins saved across the section)
- **Shadow Blocks Found:** **3 out of 5** (Zero passenger train stoppage)
- **Safety Critical Maintenance:** **100% Granted** (Urgent USFD rail flaw repaired)
