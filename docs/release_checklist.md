# Release Checklist

Use this before pushing to a **private** remote, and again before making the repository **public**.

## Data safety

- [ ] No real patient IDs in any committed file
- [ ] No files from `data/`, `project/outputs/`, or vendor extracts
- [ ] No commercial masters (医薬品マスタ, 傷病マスタ, etc.)
- [ ] No `.env`, secrets, or credentials
- [ ] Only synthetic CSV under `examples/sample_data/` and `tests/fixtures/`
- [ ] `.gitignore` blocks `*.csv` with explicit fake-data exceptions
- [ ] `git ls-files` reviewed for sensitive extensions

## Code isolation

- [ ] `grep` for study-specific codes returns **no matches in `src/`**
- [ ] Study examples live only under `examples/` and `tests/`
- [ ] Example YAML contains definitions only — no real counts or prevalences

## Quality

- [ ] `pytest` passes locally (Python 3.10+)
- [ ] GitHub Actions green on 3.10 / 3.11 / 3.12
- [ ] README includes all required disclaimers
- [ ] LICENSE matches `pyproject.toml` (Apache-2.0)
- [ ] `requires-python >= 3.10` aligned with CI

## Documentation

- [ ] `docs/data_privacy.md` complete
- [ ] `docs/code_definition_yaml.md` complete
- [ ] `docs/research_cautions.md` complete
- [ ] Examples README note: samples are not validated definitions

## Repository structure

- [ ] `jpclaims` is a **standalone repository** (not nested inside a project with real data)
- [ ] Remote is private until public checklist is signed off
- [ ] `project.urls` in `pyproject.toml` point to correct GitHub org/repo

## Human review (cannot be automated)

- [ ] Legal / IRB / data-use agreement permits open-sourcing the **code** (not data)
- [ ] Institution approves public release of example disease codes if applicable
- [ ] Author list and attribution reviewed
- [ ] No embedded credentials in git history (`git log -p` spot check)

## Public release gate

Public release is appropriate only when **all items above are checked** and CI is green.

Until then: **Private GitHub push only.**
