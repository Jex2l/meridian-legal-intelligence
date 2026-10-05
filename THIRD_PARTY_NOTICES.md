# Third-Party Notices

This project depends on open-source software. This file lists the
**direct** dependencies declared in `backend/requirements.txt`,
`frontend/package.json`, and `website/package.json`, and their licenses as
reported by each package's own metadata at the time this file was written.

**This list is not exhaustive.** It does not include transitive
dependencies (dependencies of dependencies), which can number in the
hundreds for a modern JavaScript/Python project. Before distributing this
software commercially, run a full license scan — for example
`pip-licenses` for the backend and `npx license-checker` for the frontend
apps — and have counsel review the results, particularly for any
copyleft-licensed package (LGPL, GPL, AGPL) that may impose obligations
beyond attribution.

## Backend (Python)

| Package | License |
|---|---|
| fastapi | MIT |
| uvicorn | BSD |
| sqlalchemy | MIT |
| psycopg | **LGPL-3.0** — see note below |
| pgvector | MIT |
| pydantic | MIT |
| pydantic-settings | MIT |
| python-multipart | Apache-2.0 |
| pypdf | BSD |
| pdfplumber | MIT |
| python-docx | MIT |
| pdf2image | MIT |
| pytesseract | Apache-2.0 |
| Pillow | HPND |
| sentence-transformers | Apache-2.0 |
| rank-bm25 | Apache-2.0 |
| anthropic | MIT |
| httpx | BSD |
| pytest, reportlab | (test/dev dependencies only, not shipped in production) |

**Note on psycopg (LGPL-3.0):** this is the one non-permissive license in
the direct dependency set. LGPL generally permits use as an unmodified
library dependency (as this project does) without requiring your own code
to be LGPL-licensed, but it does impose its own conditions (e.g., allowing
users to relink against a modified version of the library). Confirm LGPL
compliance with counsel before commercial distribution — this notice does
not constitute that confirmation.

## Frontend & Website (Next.js apps)

| Package | License |
|---|---|
| next | MIT |
| react | MIT |
| react-dom | MIT |
| typescript | Apache-2.0 |
| tailwindcss | MIT |

## System/External Binaries (not bundled, invoked via subprocess)

- **Tesseract OCR** (Apache-2.0) and **Poppler** (GPL-2.0/GPL-3.0 for
  `pdftoppm`, used via the `pdf2image` package) are external system
  binaries this project shells out to for OCR, not code distributed with
  this repository. If you bundle these binaries into a distributed build
  (e.g., a Docker image you ship to customers) rather than requiring them
  as a runtime system dependency, review Poppler's GPL terms with counsel.

## AI Models

- Embedding and reranker models (via `sentence-transformers`) and any
  locally-run generation model (via Ollama) are downloaded separately at
  runtime and are not distributed with this repository. Each model has its
  own license (e.g., many are Apache-2.0 or a custom model license) —
  review the specific model's license before commercial use.

---

This file was generated to accompany the MIT-licensed source code in this
repository (see [LICENSE](LICENSE)) and is provided for informational
purposes. It is not a substitute for a proper license audit.
