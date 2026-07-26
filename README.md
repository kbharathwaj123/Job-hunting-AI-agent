# AI-Powered Automated Job Application Agent

An intelligent, local, and free job application automation tool.
It automates **job discovery → company rating verification → ATS resume tailoring (local LLM) → multi-step form filling & file uploads → automatic submission & PDF reporting**.

---

## 🌟 Key Features

- **Dual Application Modes**:
  - **Online Portals Mode**: Automates LinkedIn Easy Apply, Naukri.com, and Indeed applications.
  - **Companies Official Website Mode**: Locates official company career pages and ATS engines (Workday, Greenhouse, Lever, SmartRecruiters, Taleo, ICIMS, Ashby, etc.), handles Google SSO / Account creation, auto-fills forms, and submits.
- **Automated Ollama Integration**: Checks for local LLM availability (`llama3.1:8b`) and auto-starts Ollama if offline.
- **Company Vetting & Rating Filter**: Verifies companies using online search snippets (Rating ≥ 3.5/5 and Reviews ≥ 120+) before applying.
- **Smart Form Filling Engine**: Automatically fills text inputs, numbers, phone (`tel`), email, selects (dropdowns via fuzzy matching), radio buttons, required consent checkboxes, and attaches `base_resume.docx` / `.pdf`.
- **Validation Error Recovery**: Detects form validation errors or missing mandatory field warnings, resolves the input, and re-submits.
- **Self-Healing Browser Context**: Automatically detects browser crashes or closed tabs and re-launches a fresh context seamlessly.
- **PDF Application Report**: Generates a styled, executive PDF report (`JobsApplied.pdf`) summarizing total applications, ATS match scores, company details, and emails.

---

## 🚀 Quick Setup & Installation

### 1. Prerequisites
- **Python 3.10+**
- **Ollama**: Download and install from [ollama.com](https://ollama.com/download)

### 2. Environment Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd job-agent

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\activate.ps1
# Windows CMD:
venv\Scripts\activate.bat
# Linux/macOS:
source venv/bin/activate

# Install dependencies & Playwright Chromium
pip install -r requirements.txt
playwright install chromium

# Pull Ollama LLM Model
ollama pull llama3.1:8b
```

### 3. Configuration
1. Copy the example configuration:
   ```bash
   cp config/config.example.yaml config/config.yaml
   ```
2. Open `config/config.yaml` and update your target roles, locations, salary criteria, and personal details (`profile_answers`).
3. Add your base resume to the `data/` folder:
   - `data/base_resume.docx` (used for ATS scoring and tailoring)
   - `data/base_resume.pdf` (used for file uploads)

---

## 🏃 Running the Agent

### On Windows:
Simply double-click **`run_agent.bat`**!

### Or via Terminal:
```bash
python main.py
```

Upon launching, you will be prompted:
```text
===========================================================
           JOB APPLICATION MODE SELECTION                  
===========================================================
Do you want to apply jobs through Portals or Companies Official Website?
  [1] Online Portals (LinkedIn, Naukri, Indeed)
  [2] Companies Official Website (Official Careers Pages & ATS)
===========================================================
Enter choice (1 or 2, default is 1): 
```

Once completed, check your **`Downloads`** folder for **`JobsApplied.pdf`**!

---

## 📂 Project Architecture

```
job-agent/
├── main.py                  # Main orchestrator & CLI mode prompt
├── run_agent.bat            # One-click Windows runner
├── config/
│   ├── config.yaml          # Active configuration (git-ignored)
│   └── config.example.yaml  # Template configuration
├── browser/
│   ├── session.py           # Persistent browser context launcher
│   └── form_filler.py       # Smart multi-input form filler & error recovery
├── sites/
│   ├── linkedin.py          # LinkedIn search + Easy Apply loop
│   ├── naukri_indeed.py     # Naukri & Indeed automation
│   └── company_careers.py   # Official company careers page & ATS engine
├── ats/
│   ├── scorer.py            # ATS keyword matching & resume scoring
│   └── company_check.py     # Company rating & review verification
├── resume/
│   ├── tailor.py            # Resume summary & bullet point tailoring via Ollama
│   └── report.py            # PDF report generator (JobsApplied.pdf)
└── data/
    ├── db.py                # SQLite application tracking & status logging
    ├── base_resume.docx     # Your primary resume (git-ignored)
    ├── base_resume.pdf      # Your PDF resume (git-ignored)
    ├── applications.db      # Local application history (git-ignored)
    └── browser_profile/     # Persistent browser session & cookies (git-ignored)
```

---

## 🔒 Security & Privacy

- **No Stored Passwords**: Uses a persistent Chromium user profile (`data/browser_profile/`). You log into sites manually once, and session cookies are reused.
- **Git Safety**: All personal files (`base_resume.docx`, `applications.db`, `browser_profile/`, `config.yaml`) are strictly ignored by `.gitignore`.
