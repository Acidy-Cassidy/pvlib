# pvlib

A personal “utility library” repo of lightweight, self-contained **my\*** modules that mirror common Python libraries (for learning, experimentation, and quick bootstrapping), plus a few small test programs. 

This repository is intentionally simple and modular, designed for:
- learning how common Python libraries work internally
- quickly validating Python environments
- bootstrapping scripts without pulling in large dependencies 

---

## Project Goals & Philosophy

The primary goal of **pvlib** is to serve as a **personal, evolving repository of custom-built and commonly used Python libraries**.

This project exists to:
- **Re-implement and wrap familiar libraries**  
  Build simplified versions of popular tools (NumPy, Pandas, tqdm, etc.) to better understand their structure, patterns, and design decisions. 
- **Create a personal standard toolkit**  
  Maintain a trusted set of utilities that can be reused across many projects without starting from scratch. 
- **Enable rapid experimentation**  
  Quickly test ideas, environments, and scripts without relying on heavyweight dependencies or complex installs. 
- **Deepen Python mastery**  
  Reinforce fundamentals such as iteration, data handling, testing, system inspection, plotting, and I/O by implementing them directly. 
- **Act as a living learning log**  
  This repository is intentionally unfinished and evolving as new libraries are explored, rewritten, or extended. 

This project is **not** intended to replace production-grade libraries. Instead, it prioritizes:
- clarity over completeness
- readability over performance
- understanding over abstraction 

---

## Included Modules

Current modules mirror familiar Python libraries (each one is intentionally minimal and readable): 

- `mynumpy/` – NumPy-style helpers and array utilities 
- `mypandas/` – Pandas-style helpers for basic data handling 
- `mytqdm/` – lightweight progress / iteration helpers 
- `myrequests/` – simple HTTP request wrappers 
- `mypsutil/` – system and resource inspection helpers 
- `mypytest/` – quick testing / validation helpers 
- `mycolorama/` – terminal color / formatting helpers 
- `mymatplotlib/` – plotting helper wrappers 
- `mybeautifulsoup/` – BeautifulSoup-style HTML parsing / scraping helpers (new) 

> Naming convention: modules are prefixed with `my` to make it obvious they’re educational/experimental re-implementations and not drop-in replacements.

---

## Repo Layout

At the repo root you’ll find the modules plus a few helper/reference files: 

- `INSTALL.txt` – install notes 
- `LIBRARIES.txt` – dependency notes / library list 
- `install.sh` – helper installer script 
- `test_libs.py` – general smoke test for installed/importable libs 

---

## Quick Start

### 1) Clone the repo
```bash
git clone https://github.com/Acidy-Cassidy/pvlib.git
cd pvlib
