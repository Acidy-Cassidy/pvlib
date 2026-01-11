# pvlib

A personal “utility library” repo of lightweight, self-contained **my\*** modules that mirror common Python libraries (for learning, experimentation, and quick bootstrapping), plus a few small test programs. :contentReference[oaicite:0]{index=0}

This repository is intentionally simple and modular, designed for:
- learning how common Python libraries work internally
- quickly validating Python environments
- bootstrapping scripts without pulling in large dependencies :contentReference[oaicite:1]{index=1}

---

## Project Goals & Philosophy

The primary goal of **pvlib** is to serve as a **personal, evolving repository of custom-built and commonly used Python libraries**. :contentReference[oaicite:2]{index=2}

This project exists to:
- **Re-implement and wrap familiar libraries**  
  Build simplified versions of popular tools (NumPy, Pandas, tqdm, etc.) to better understand their structure, patterns, and design decisions. :contentReference[oaicite:3]{index=3}
- **Create a personal standard toolkit**  
  Maintain a trusted set of utilities that can be reused across many projects without starting from scratch. :contentReference[oaicite:4]{index=4}
- **Enable rapid experimentation**  
  Quickly test ideas, environments, and scripts without relying on heavyweight dependencies or complex installs. :contentReference[oaicite:5]{index=5}
- **Deepen Python mastery**  
  Reinforce fundamentals such as iteration, data handling, testing, system inspection, plotting, and I/O by implementing them directly. :contentReference[oaicite:6]{index=6}
- **Act as a living learning log**  
  This repository is intentionally unfinished and evolving as new libraries are explored, rewritten, or extended. :contentReference[oaicite:7]{index=7}

This project is **not** intended to replace production-grade libraries. Instead, it prioritizes:
- clarity over completeness
- readability over performance
- understanding over abstraction :contentReference[oaicite:8]{index=8}

---

## Included Modules

Current modules mirror familiar Python libraries (each one is intentionally minimal and readable): :contentReference[oaicite:9]{index=9}

- `mynumpy/` – NumPy-style helpers and array utilities :contentReference[oaicite:10]{index=10}
- `mypandas/` – Pandas-style helpers for basic data handling :contentReference[oaicite:11]{index=11}
- `mytqdm/` – lightweight progress / iteration helpers :contentReference[oaicite:12]{index=12}
- `myrequests/` – simple HTTP request wrappers :contentReference[oaicite:13]{index=13}
- `mypsutil/` – system and resource inspection helpers :contentReference[oaicite:14]{index=14}
- `mypytest/` – quick testing / validation helpers :contentReference[oaicite:15]{index=15}
- `mycolorama/` – terminal color / formatting helpers :contentReference[oaicite:16]{index=16}
- `mymatplotlib/` – plotting helper wrappers :contentReference[oaicite:17]{index=17}
- `mybeautifulsoup/` – BeautifulSoup-style HTML parsing / scraping helpers (new) :contentReference[oaicite:18]{index=18}

> Naming convention: modules are prefixed with `my` to make it obvious they’re educational/experimental re-implementations and not drop-in replacements.

---

## Repo Layout

At the repo root you’ll find the modules plus a few helper/reference files: :contentReference[oaicite:19]{index=19}

- `INSTALL.txt` – install notes :contentReference[oaicite:20]{index=20}
- `LIBRARIES.txt` – dependency notes / library list :contentReference[oaicite:21]{index=21}
- `install.sh` – helper installer script :contentReference[oaicite:22]{index=22}
- `test_libs.py` – general smoke test for installed/importable libs :contentReference[oaicite:23]{index=23}

---

## Quick Start

### 1) Clone the repo
```bash
git clone https://github.com/Acidy-Cassidy/pvlib.git
cd pvlib
