# 🔍 DocInvestigator: Intelligent Document Investigator
### Cross-Document Comparison, Conflict Detection & Evidence-Backed Q&A Platform
**Algothon '26 Submission | Problem Statement: ALG-AI-02 (AI / ML Domain)**

---

## 💡 The Core Problem & Our Innovation

### The Problem
In enterprise investigations (M&A due diligence, legal contract reviews, clinical trials, and cyber breach post-mortems), critical information is scattered across dozens of documents, spreadsheets, and reports. 

### The Flaw in Existing Solutions (Standard RAG)
Existing document Q&A and RAG systems make a fatal assumption: **they assume all documents agree with each other**.
When presented with contradictory facts (e.g., Document A states the acquisition price is **$50,000,000**, while the forensic audit in Document B restates it to **$41,800,000**), standard RAG will either:
1. Arbitrarily pick whichever chunk had a slightly higher embedding score,
2. Hallucinate an ungrounded compromise, or
3. Confidently return one answer while completely ignoring the discrepancy.

### Our Solution: The Investigation Layer
**DocInvestigator** builds an active **Investigation Layer** over multi-document Q&A:
- **Balanced Multi-Doc Sourcing (BMDS)**: Guarantees candidate chunks from *every* ingested document are examined so divergent claims cannot be silenced.
- **Cross-Document Conflict & Contradiction Detection**: Automatically extracts numerical, temporal, status/polarity, and categorical claims and detects disagreements across documents.
- **Uncertainty & Divergence Communication (Algothon Bonus)**: Rather than returning a single misleading answer, the engine flags conflicts with an active warning banner, classifies certainty (`CONFLICT_DETECTED`, `UNVERIFIED_SINGLE_SOURCE`, `CONSENSUS_VERIFIED`), and generates an interactive side-by-side clause diff.
- **Strict Evidence Grounding**: Every finding cites exact document names, sections, page numbers, and verbatim quotes.

---

## 🏆 Algothon'26 Requirements Mapping

| Requirement (ALG-AI-02) | DocInvestigator Implementation | Verification in Prototype |
| :--- | :--- | :--- |
| **Multiple document formats** | Supports Markdown, Plain Text, PDF (pypdf/stream parser), CSV, and JSON structures. | Verified via `DocumentProcessor` in `backend/document_processor.py`. |
| **Extraction & Indexing** | Section-aware chunking preserving headings, page numbers, and character spans; hybrid BM25 + inverted index. | Verified via `DocumentIndex` in `backend/retriever.py`. |
| **Natural-language Q&A** | In-depth investigative queries answered with executive summaries, discrepancies, and recommendations. | REST endpoint `POST /api/investigate`. |
| **Source/Section references** | Exact citations with `[DocName, Page X, Section Y]` and verbatim quotes. | Rendered in "Cited Evidence Chunks" panel and export report. |
| **Conflict detection** | Automated extraction of currency, dates, percentages, and negation polarities with pairwise cross-doc alignment. | Visualized in the **Cross-Doc Conflict Matrix** and contradiction alert cards. |
| **Uncertainty handling** | Explicit certainty scoring badges: `CONFLICT_DETECTED`, `SINGLE_SOURCE_UNVERIFIED`, `CROSS_VERIFIED`. | Top banner pulses red when contradictory facts exist. |
| **Innovation / Bonus** | **Side-by-Side Clause Alignment Inspector** & pairwise conflict heatmap rather than blindly returning one answer. | Click "Compare Clauses" to view conflicting passages side-by-side. |

---

## ⚡ Quickstart: Running the Working Prototype

The application is engineered with **Zero Mandatory Dependencies**: it runs immediately with standard Python 3.9+ using the built-in HTTP server, while also supporting FastAPI/Uvicorn if installed.

### 1. Launch the Server

#### On Windows:
Double-click `run.bat` or run in terminal:
```cmd
cd intelligent-doc-investigator
python app.py
```

#### On Linux / macOS:
```bash
chmod +x run.sh
./run.sh
```

### 2. Open the Web Application
Open your browser to:
👉 **`http://localhost:8000`**

---

## 🧪 Interactive Benchmark Demonstrations (1-Click Evaluation)

The prototype comes pre-loaded with **3 curated investigation dossiers** designed to test edge cases and conflict handling:

### Benchmark 1: M&A Acquisition Due Diligence ("Project Phoenix")
- **Documents**: 4 documents (Confidential Information Memorandum, Forensic Audit Report, Board Meeting Minutes, Legal IP Due Diligence).
- **Embedded Conflicts**:
  - 💰 **Valuation Discrepancy**: Memorandum claims **$50,000,000**, Forensic Audit restates it to **$41,800,000**, and Board Minutes caps it at **$44,000,000**.
  - 📅 **Timeline Conflict**: Memorandum specifies closing on **October 15, 2026**; Board Minutes moves closing to **November 30, 2026**.
  - ⚖️ **IP Liability Clash**: Memorandum asserts IP is 100% clean; Legal Audit reveals core engine is contaminated with **GNU GPL v3.0**.
- **Test Query**: *"What is the agreed purchase price and valuation for Project Phoenix?"*

### Benchmark 2: Clinical Trial Safety & Dosage ("Trial CT-904")
- **Documents**: Protocol Document vs. DSMB Emergency Safety Advisory.
- **Embedded Conflicts**:
  - 💊 **Dosage Conflict**: Protocol authorizes **100 mg/day**; Safety Advisory slashes maximum dose to **50 mg/day** due to hepatotoxicity.
  - 👥 **Age Eligibility**: Protocol includes patients aged **65-75**; Safety Advisory strictly **prohibits** patients > 65.
  - ⏱️ **Monitoring Interval**: Protocol specifies **monthly** tests; Safety Advisory orders **weekly** tests.
- **Test Query**: *"What is the approved daily dosage for study drug CT-904?"*

### Benchmark 3: Cyber Incident DFIR Response
- **Documents**: Internal SOC Incident Log vs. External IronClad Forensics Report.
- **Embedded Conflicts**:
  - ⏰ **Breach Timestamp**: SOC logs ingress on **Aug 14 at 03:15 UTC**; Forensics proves ingress was **Aug 11 at 22:40 UTC** (53 hours earlier).
  - 🖥️ **Impacted Servers**: SOC reports **4 servers**; Forensics confirms **19 servers** compromised.
  - 📁 **Data Exfiltration**: SOC claims no PII was stolen; Forensics confirms **84 GB (450,000 records)** exfiltrated via DNS tunneling.
- **Test Query**: *"How many production servers were compromised during the incident?"*

---

## 🛠️ System Architecture

```
intelligent-doc-investigator/
├── app.py                      # Multi-mode Web Server (FastAPI + Zero-dep http.server)
├── backend/
│   ├── document_processor.py   # Multi-format parser & structure-aware chunker
│   ├── retriever.py            # Balanced Multi-Doc Sourcing (BMDS) & Okapi BM25
│   ├── conflict_detector.py    # Claim extraction, pairwise alignment & conflict engine
│   ├── investigation_engine.py # Orchestrator for retrieval, conflict analysis & synthesis
│   ├── gemini_client.py        # Gemini API integration with local deterministic fallback
│   └── sample_data.py          # Benchmark investigation dossiers
├── frontend/
│   ├── index.html              # Modern, responsive investigative dashboard (Tailwind CSS)
│   ├── styles.css              # Custom styling, dark scrollbars, conflict pulse animations
│   └── app.js                  # State management, conflict matrix, modal diffs & report export
├── tests/
│   ├── test_conflict_detector.py # Unit tests for numerical, temporal & polarity conflicts
│   ├── test_retriever.py       # Unit tests for BMDS & section boundary preservation
│   └── test_investigation.py   # End-to-end integration tests on benchmark dossiers
├── ARCHITECTURE.md             # In-depth architectural & mathematical documentation
├── requirements.txt            # Optional extended packages (FastAPI, pypdf, google-genai)
├── run.bat                     # Windows 1-click startup script
├── run.sh                      # Linux/Mac startup script
└── README.md                   # Submission documentation & evaluation rubric mapping
```

---

## 🔬 Testing Evidence & Verification

Run the automated test suite with standard Python:

```bash
# Run Conflict Detection Unit Tests
python tests/test_conflict_detector.py

# Run Multi-Doc Sourcing Retriever Tests
python tests/test_retriever.py

# Run End-to-End Investigation Integration Tests
python tests/test_investigation.py
```

### Test Results Summary:
- ✅ `test_numerical_conflict_detection`: Successfully detected valuation mismatch ($50M vs $41.8M) with `HIGH` severity.
- ✅ `test_temporal_date_conflict_detection`: Successfully detected closing date divergence (Oct 15 vs Nov 30).
- ✅ `test_polarity_contradiction_detection`: Correctly detected affirmative vs negated assertion (*clean* vs *not cleanly owned*).
- ✅ `test_consensus_agreement`: Verified that matching claims across documents are classified as `CONSENSUS_VERIFIED`.
- ✅ `test_balanced_multi_doc_retrieval`: Validated that short contradictory documents are never masked by long documents in BMDS retrieval.

---

## 🌐 External APIs & AI Disclosure

In accordance with Algothon'26 common submission expectations (Slide 39):
- **Core Engine**: Fully implemented in pure Python with **zero external API dependencies required**.
- **Optional Generative Synthesis**: Can integrate with Google Gemini (`gemini-2.5-flash` or `gemini-1.5-pro`) by providing a `GEMINI_API_KEY` in the UI or environment variable.
- **Offline Reliability**: When running without an API key, the system uses its internal deterministic symbolic synthesis engine, guaranteeing 100% functionality even during venue connectivity outages.

---

## 🚀 Known Limitations & Future Roadmap

1. **OCR for Scanned Hand-Drawn Diagrams**: Current extraction supports text, PDFs, and structured data; integration with multimodal vision models (e.g. Gemini Vision) would allow inspecting handwriting on legacy deeds.
2. **Autonomous Stakeholder Notification**: Future versions could automatically draft clarification emails to authors of contradictory documents to reconcile differences in real-time.
3. **Temporal Supersedence Graph**: Automatically parsing document revision histories and signing dates to algorithmically calculate which document legally supersedes another.
