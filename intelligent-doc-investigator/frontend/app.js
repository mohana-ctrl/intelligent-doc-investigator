/**
 * Intelligent Document Investigator - Frontend Application Controller
 * Handles cross-document Q&A, conflict matrix rendering, side-by-side diffing,
 * benchmark switching, and report exporting.
 * Features automatic fallback for direct file opening (file://) or live server (http://).
 */

// Application State
const state = {
  currentDossier: 'ma_due_diligence',
  documents: [],
  activeConflicts: [],
  matrixData: null,
  lastInvestigationResult: null,
  isLiveServer: true
};

// DOM Elements
const docCountEl = document.getElementById('docCount');
const activeDossierTitleEl = document.getElementById('activeDossierTitle');
const activeDossierDescEl = document.getElementById('activeDossierDesc');
const documentListEl = document.getElementById('documentList');
const suggestedChipsEl = document.getElementById('suggestedChips');
const benchmarkSelector = document.getElementById('benchmarkSelector');
const loadBenchmarkBtn = document.getElementById('loadBenchmarkBtn');
const investigationForm = document.getElementById('investigationForm');
const queryInput = document.getElementById('queryInput');
const runInvestigateBtn = document.getElementById('runInvestigateBtn');

// Banner & Results Elements
const certaintyBanner = document.getElementById('certaintyBanner');
const certaintyTag = document.getElementById('certaintyTag');
const certaintyHeadline = document.getElementById('certaintyHeadline');
const certaintyIconContainer = document.getElementById('certaintyIconContainer');
const evidenceSourceCount = document.getElementById('evidenceSourceCount');
const discrepancyBox = document.getElementById('discrepancyBox');
const discrepancyList = document.getElementById('discrepancyList');
const answerMarkdown = document.getElementById('answerMarkdown');
const llmEngineTag = document.getElementById('llmEngineTag');
const citationsGrid = document.getElementById('citationsGrid');
const citationCount = document.getElementById('citationCount');

// Matrix & Right Rail
const matrixTableContainer = document.getElementById('matrixTableContainer');
const conflictFeed = document.getElementById('conflictFeed');
const conflictBadgeTotal = document.getElementById('conflictBadgeTotal');

// Modals
const uploadModal = document.getElementById('uploadModal');
const openUploadModalBtn = document.getElementById('openUploadModalBtn');
const closeUploadModalBtn = document.getElementById('closeUploadModalBtn');
const cancelUploadBtn = document.getElementById('cancelUploadBtn');
const submitUploadBtn = document.getElementById('submitUploadBtn');

const configModal = document.getElementById('configModal');
const openConfigBtn = document.getElementById('openConfigBtn');
const closeConfigModalBtn = document.getElementById('closeConfigModalBtn');
const cancelConfigBtn = document.getElementById('cancelConfigBtn');
const saveConfigBtn = document.getElementById('saveConfigBtn');
const geminiApiKeyInput = document.getElementById('geminiApiKeyInput');
const llmModeText = document.getElementById('llmModeText');

const clauseCompareModal = document.getElementById('clauseCompareModal');
const closeCompareModalBtn = document.getElementById('closeCompareModalBtn');
const closeCompareModalBtn2 = document.getElementById('closeCompareModalBtn2');
const compareModalTitle = document.getElementById('compareModalTitle');
const compareModalSubtitle = document.getElementById('compareModalSubtitle');
const compareModalBody = document.getElementById('compareModalBody');

const exportReportBtn = document.getElementById('exportReportBtn');
const viewMatrixBtn = document.getElementById('viewMatrixBtn');

// Client-Side Fallback Benchmark Data (Enables 100% offline standalone direct HTML viewing)
const CLIENT_FALLBACK_DATA = {
  ma_due_diligence: {
    documents: [
      { doc_id: 'phoenix_cim', doc_name: 'Project_Phoenix_Confidential_Memorandum.md', chunk_count: 4, sections: ['Executive Summary', 'Financial Metrics', 'Closing Schedule', 'IP Rights'] },
      { doc_id: 'phoenix_audit', doc_name: 'Independent_Financial_Audit_Report.md', chunk_count: 3, sections: ['Valuation Restatement', 'Restated EBITDA', 'Timeline Considerations'] },
      { doc_id: 'phoenix_board', doc_name: 'Special_Board_Meeting_Minutes.md', chunk_count: 3, sections: ['Review of Discrepancies', 'Revised Closing Milestone'] },
      { doc_id: 'phoenix_legal_ip', doc_name: 'Legal_Codebase_IP_Assessment.md', chunk_count: 3, sections: ['Scope of Audit', 'Open Source Infringements', 'IP Conclusion'] }
    ],
    matrix: {
      document_names: ['Project_Phoenix_Confidential_Memorandum.md', 'Independent_Financial_Audit_Report.md', 'Special_Board_Meeting_Minutes.md', 'Legal_Codebase_IP_Assessment.md'],
      matrix: {
        'Project_Phoenix_Confidential_Memorandum.md': { 'Project_Phoenix_Confidential_Memorandum.md': 0, 'Independent_Financial_Audit_Report.md': 1, 'Special_Board_Meeting_Minutes.md': 2, 'Legal_Codebase_IP_Assessment.md': 1 },
        'Independent_Financial_Audit_Report.md': { 'Project_Phoenix_Confidential_Memorandum.md': 1, 'Independent_Financial_Audit_Report.md': 0, 'Special_Board_Meeting_Minutes.md': 1, 'Legal_Codebase_IP_Assessment.md': 0 },
        'Special_Board_Meeting_Minutes.md': { 'Project_Phoenix_Confidential_Memorandum.md': 2, 'Independent_Financial_Audit_Report.md': 1, 'Special_Board_Meeting_Minutes.md': 0, 'Legal_Codebase_IP_Assessment.md': 0 },
        'Legal_Codebase_IP_Assessment.md': { 'Project_Phoenix_Confidential_Memorandum.md': 1, 'Independent_Financial_Audit_Report.md': 0, 'Special_Board_Meeting_Minutes.md': 0, 'Legal_Codebase_IP_Assessment.md': 0 }
      },
      conflict_count: 3,
      conflicts: [
        {
          topic: 'Valuation & Purchase Price',
          type: 'NUMERICAL_MISMATCH',
          involved_documents: ['Project_Phoenix_Confidential_Memorandum.md', 'Independent_Financial_Audit_Report.md', 'Special_Board_Meeting_Minutes.md'],
          description: "CIM asserts valuation is $50,000,000 USD ($50M); Independent Audit restates fair valuation to $41,800,000 USD; Board Minutes strictly prohibits transaction above $44,000,000 USD.",
          advice: "Financial figures diverge by $8.2M. Reconcile working capital adjustments and request formal audit signoff."
        },
        {
          topic: 'Closing & Execution Date',
          type: 'TEMPORAL_MISMATCH',
          involved_documents: ['Project_Phoenix_Confidential_Memorandum.md', 'Special_Board_Meeting_Minutes.md'],
          description: "Memorandum states closing on October 15, 2026; Board Resolution 4B formally postponed closing to November 30, 2026.",
          advice: "Examine board amendment dated Oct 2, 2026 which legally supersedes the earlier memorandum schedule."
        },
        {
          topic: 'Intellectual Property & Codebase Ownership',
          type: 'POLARITY_CONTRADICTION',
          involved_documents: ['Project_Phoenix_Confidential_Memorandum.md', 'Legal_Codebase_IP_Assessment.md'],
          description: "CIM guarantees IP is 100% clean and free of third-party licenses; Legal IP Audit reveals core engine uses GNU GPL v3.0 without attribution.",
          advice: "Remediation cost estimated at $1.8M and 4 months delay. Require escrow indemnification."
        }
      ]
    },
    default_result: {
      query: "What is the agreed purchase price and valuation for Project Phoenix?",
      certainty: "CONFLICT_DETECTED",
      llm_status: "Deterministic Investigation Engine (ALG-AI-02)",
      answer: "### 🔍 Executive Investigation Summary\n**Query**: *\"What is the agreed purchase price and valuation for Project Phoenix?\"*\n**Cross-Document Certainty**: `CRITICAL DISCREPANCY DETECTED`\n**Examined Sources**: 4 evidence passages across 3 documents.\n\n### ⚠️ Critical Cross-Document Discrepancies\n> [!WARNING] **Contradictory valuation figures identified between primary sources.** Standard RAG would average or silence this divergence; our investigation layer isolates it:\n\n- **Valuation & Purchase Price** (`NUMERICAL_MISMATCH`): Direct numeric discrepancy detected across 3 documents: 'Project_Phoenix_Confidential_Memorandum.md': $50,000,000 USD ($50M); 'Independent_Financial_Audit_Report.md': $41,800,000 USD ($41.8M); 'Special_Board_Meeting_Minutes.md': $44,000,000 cap.\n  *Investigator Guidance*: Conflicting figures indicate audit revisions. Review forensic adjustments before contract signing.\n    • **[Project_Phoenix_Confidential_Memorandum.md, Page 1, §1. Executive Summary]**: \"The enterprise valuation agreed upon for this transaction is $50,000,000 USD ($50M).\"\n    • **[Independent_Financial_Audit_Report.md, Page 1, §SECTION 1: Valuation Restatement]**: \"Our revised valuation firmly establishes the fair enterprise valuation at $41,800,000 USD ($41.8M), representing a significant downgrade from the $50,000,000 claimed in the memorandum.\"\n    • **[Special_Board_Meeting_Minutes.md, Page 1, §2. Review of Project Phoenix Discrepancies]**: \"Resolution 4B: The Board voted unanimously NOT to approve any transaction exceeding $44,000,000.\"\n\n### 📋 Investigator Recommendation\nBecause conflicting valuations exist across documents, do **not** execute binding documents without reconciling Delmar & Hastings forensic audit findings.",
      citations: [
        { doc_name: "Project_Phoenix_Confidential_Memorandum.md", section: "1. Executive Summary", page_num: 1, chunk_id: "phoenix_cim_c0", excerpt: "The enterprise valuation agreed upon for this transaction is $50,000,000 USD ($50M). The proposed transaction structure is 80% cash and 20% stock equity." },
        { doc_name: "Independent_Financial_Audit_Report.md", section: "SECTION 1: Valuation Restatement", page_num: 1, chunk_id: "phoenix_audit_p1_c0", excerpt: "Our revised valuation firmly establishes the fair enterprise valuation at $41,800,000 USD ($41.8M), representing a significant downgrade from the $50,000,000 claimed in the memorandum." },
        { doc_name: "Special_Board_Meeting_Minutes.md", section: "2. Review of Project Phoenix Discrepancies", page_num: 1, chunk_id: "phoenix_board_c1", excerpt: "Resolution 4B: The Board voted unanimously NOT to approve any transaction exceeding $44,000,000. CEO Sterling is instructed to reopen price negotiations immediately." }
      ],
      conflicts: [
        {
          topic: "Valuation & Purchase Price",
          conflict_type: "NUMERICAL_MISMATCH",
          severity: "HIGH",
          description: "Memorandum states $50,000,000; Independent Audit reduces to $41,800,000; Board caps at $44,000,000.",
          investigator_advice: "Reopen price negotiations and establish working capital escrow.",
          claims: [
            { doc_name: "Project_Phoenix_Confidential_Memorandum.md", page_num: 1, section: "Executive Summary", quote: "The enterprise valuation agreed upon for this transaction is $50,000,000 USD ($50M).", value_raw: "$50,000,000 USD", value_type: "currency", chunk_id: "phoenix_cim_c0" },
            { doc_name: "Independent_Financial_Audit_Report.md", page_num: 1, section: "Valuation Restatement", quote: "Our revised valuation firmly establishes the fair enterprise valuation at $41,800,000 USD ($41.8M).", value_raw: "$41,800,000 USD", value_type: "currency", chunk_id: "phoenix_audit_p1_c0" }
          ]
        }
      ],
      documents_consulted: ["Project_Phoenix_Confidential_Memorandum.md", "Independent_Financial_Audit_Report.md", "Special_Board_Meeting_Minutes.md"]
    }
  },
  clinical_safety: {
    documents: [
      { doc_id: 'clinical_protocol', doc_name: 'Clinical_Trial_Protocol_v4.md', chunk_count: 3, sections: ['Dosing Schedule', 'Inclusion & Exclusion', 'Laboratory Monitoring'] },
      { doc_id: 'safety_advisory', doc_name: 'Data_Safety_Monitoring_Board_Urgent_Advisory.md', chunk_count: 3, sections: ['Hepatotoxicity Warning', 'Emergency Exclusion', 'Intensified Monitoring'] }
    ],
    matrix: {
      document_names: ['Clinical_Trial_Protocol_v4.md', 'Data_Safety_Monitoring_Board_Urgent_Advisory.md'],
      matrix: {
        'Clinical_Trial_Protocol_v4.md': { 'Clinical_Trial_Protocol_v4.md': 0, 'Data_Safety_Monitoring_Board_Urgent_Advisory.md': 3 },
        'Data_Safety_Monitoring_Board_Urgent_Advisory.md': { 'Clinical_Trial_Protocol_v4.md': 3, 'Data_Safety_Monitoring_Board_Urgent_Advisory.md': 0 }
      },
      conflict_count: 3,
      conflicts: [
        {
          topic: 'Dosage & Protocol Guidelines',
          type: 'NUMERICAL_MISMATCH',
          involved_documents: ['Clinical_Trial_Protocol_v4.md', 'Data_Safety_Monitoring_Board_Urgent_Advisory.md'],
          description: "Protocol approves 100 mg/day; DSMB Emergency Advisory slashes maximum dose to 50 mg/day due to Grade 3 hepatotoxicity.",
          advice: "Do not dose at 100 mg/day. DSMB safety order takes immediate priority over base protocol."
        },
        {
          topic: 'Patient Eligibility Criteria',
          type: 'POLARITY_CONTRADICTION',
          involved_documents: ['Clinical_Trial_Protocol_v4.md', 'Data_Safety_Monitoring_Board_Urgent_Advisory.md'],
          description: "Protocol includes patients aged 65-75; DSMB advisory strictly excludes all patients over 65 years.",
          advice: "Suspend enrollment of patients >65 immediately to comply with institutional safety regulations."
        }
      ]
    },
    default_result: {
      query: "What is the approved daily dosage for study drug CT-904?",
      certainty: "CONFLICT_DETECTED",
      llm_status: "Deterministic Investigation Engine (ALG-AI-02)",
      answer: "### 🔍 Executive Investigation Summary\n**Query**: *\"What is the approved daily dosage for study drug CT-904?\"*\n**Cross-Document Certainty**: `CRITICAL DISCREPANCY DETECTED`\n**Examined Sources**: 2 documents with direct safety contradictions.\n\n### ⚠️ Critical Cross-Document Discrepancies\n- **Dosage & Protocol Guidelines** (`NUMERICAL_MISMATCH`): Base Protocol authorizes **100 mg/day**, but DSMB Urgent Advisory restricts maximum allowable dose to **50 mg/day**.\n  *Investigator Guidance*: Immediate medical safety alert: DSMB Advisory #04 supersedes Protocol v4.\n    • **[Clinical_Trial_Protocol_v4.md, Page 1, §1. Dosing Schedule]**: \"The therapeutic target dosage is 100 mg/day administered orally in two 50 mg increments.\"\n    • **[Data_Safety_Monitoring_Board_Urgent_Advisory.md, Page 1, §1. Safety Signal Warning: Hepatotoxicity]**: \"Effective immediately, the maximum allowable dosage is reduced from 100 mg/day to 50 mg/day. No patient may receive 100 mg/day under any circumstances.\"",
      citations: [
        { doc_name: "Clinical_Trial_Protocol_v4.md", section: "1. Dosing Schedule", page_num: 1, chunk_id: "c_p1", excerpt: "The therapeutic target dosage is 100 mg/day administered orally in two 50 mg increments." },
        { doc_name: "Data_Safety_Monitoring_Board_Urgent_Advisory.md", section: "1. Safety Signal Warning", page_num: 1, chunk_id: "c_p2", excerpt: "Effective immediately, the maximum allowable dosage is reduced from 100 mg/day to 50 mg/day." }
      ],
      conflicts: [
        {
          topic: "Dosage & Protocol Guidelines",
          conflict_type: "NUMERICAL_MISMATCH",
          severity: "HIGH",
          description: "Protocol permits 100 mg/day; DSMB restricts to 50 mg/day.",
          investigator_advice: "Follow DSMB restriction immediately.",
          claims: [
            { doc_name: "Clinical_Trial_Protocol_v4.md", page_num: 1, section: "Dosing Schedule", quote: "The therapeutic target dosage is 100 mg/day.", value_raw: "100 mg/day", value_type: "numeric", chunk_id: "c_p1" },
            { doc_name: "Data_Safety_Monitoring_Board_Urgent_Advisory.md", page_num: 1, section: "Safety Signal Warning", quote: "The maximum allowable dosage is reduced from 100 mg/day to 50 mg/day.", value_raw: "50 mg/day", value_type: "numeric", chunk_id: "c_p2" }
          ]
        }
      ],
      documents_consulted: ["Clinical_Trial_Protocol_v4.md", "Data_Safety_Monitoring_Board_Urgent_Advisory.md"]
    }
  },
  cyber_incident: {
    documents: [
      { doc_id: 'soc_alert_log', doc_name: 'SOC_Security_Operations_Incident_Log.md', chunk_count: 3, sections: ['Detection Timeline', 'Compromised Assets', 'Data Exfiltration'] },
      { doc_id: 'external_forensics', doc_name: 'Mandiant_External_Forensics_Final_Report.md', chunk_count: 3, sections: ['Ingress Timeline', 'True Blast Radius', 'Exfiltration Verification'] }
    ],
    matrix: {
      document_names: ['SOC_Security_Operations_Incident_Log.md', 'Mandiant_External_Forensics_Final_Report.md'],
      matrix: {
        'SOC_Security_Operations_Incident_Log.md': { 'SOC_Security_Operations_Incident_Log.md': 0, 'Mandiant_External_Forensics_Final_Report.md': 3 },
        'Mandiant_External_Forensics_Final_Report.md': { 'SOC_Security_Operations_Incident_Log.md': 3, 'Mandiant_External_Forensics_Final_Report.md': 0 }
      },
      conflict_count: 3,
      conflicts: [
        {
          topic: 'Security Incident Scope & Impact',
          type: 'NUMERICAL_MISMATCH',
          involved_documents: ['SOC_Security_Operations_Incident_Log.md', 'Mandiant_External_Forensics_Final_Report.md'],
          description: "Internal SOC logs report only 4 servers accessed; Independent DFIR forensics proves 19 production servers compromised.",
          advice: "Revoke all administrative domain credentials; SOC initial triage severely under-scoped the blast radius."
        }
      ]
    },
    default_result: {
      query: "How many production servers were compromised during the incident?",
      certainty: "CONFLICT_DETECTED",
      llm_status: "Deterministic Investigation Engine (ALG-AI-02)",
      answer: "### 🔍 Executive Investigation Summary\n**Query**: *\"How many production servers were compromised during the incident?\"*\n**Cross-Document Certainty**: `CRITICAL DISCREPANCY DETECTED`\n**Examined Sources**: 2 forensic incident reports.\n\n### ⚠️ Critical Cross-Document Discrepancies\n- **Security Incident Scope & Impact** (`NUMERICAL_MISMATCH`): The internal SOC report estimated **4 servers**, whereas IronClad Digital Forensics identified **19 servers** compromised.\n  *Investigator Guidance*: Initial SOC telemetry missed lateral movement across database mirrors.",
      citations: [
        { doc_name: "SOC_Security_Operations_Incident_Log.md", section: "2. Compromised Asset Count", page_num: 1, chunk_id: "soc_c1", excerpt: "Security telemetry indicates 4 production servers were accessed by the intruder: web-app-01, web-app-02, db-auth-01, and proxy-01." },
        { doc_name: "Mandiant_External_Forensics_Final_Report.md", section: "SECTION 2: True Blast Radius", page_num: 2, chunk_id: "forensics_c2", excerpt: "The attacker achieved domain administrator privilege escalation. A total of 19 production servers were compromised, including active database mirrors." }
      ],
      conflicts: [
        {
          topic: "Security Incident Scope & Impact",
          conflict_type: "NUMERICAL_MISMATCH",
          severity: "HIGH",
          description: "SOC reported 4 servers; Forensics proved 19 servers.",
          investigator_advice: "Expand containment perimeter to all 19 identified nodes.",
          claims: [
            { doc_name: "SOC_Security_Operations_Incident_Log.md", page_num: 1, section: "Compromised Asset Count", quote: "Security telemetry indicates 4 production servers were accessed.", value_raw: "4 servers", value_type: "numeric", chunk_id: "soc_c1" },
            { doc_name: "Mandiant_External_Forensics_Final_Report.md", page_num: 2, section: "True Blast Radius", quote: "A total of 19 production servers were compromised.", value_raw: "19 servers", value_type: "numeric", chunk_id: "forensics_c2" }
          ]
        }
      ],
      documents_consulted: ["SOC_Security_Operations_Incident_Log.md", "Mandiant_External_Forensics_Final_Report.md"]
    }
  }
};

// Initialize on load
document.addEventListener('DOMContentLoaded', async () => {
  if (window.lucide) {
    window.lucide.createIcons();
  }
  await fetchHealthAndConfig();
  await loadDocuments();
  await loadConflictMatrix();
  renderBenchmarkChips();

  // Run initial investigation
  executeInvestigation();
});

// Setup Lucide helper
function refreshIcons() {
  if (window.lucide) {
    window.lucide.createIcons();
  }
}

// 1. Health & Configuration
async function fetchHealthAndConfig() {
  try {
    const res = await fetch('/api/health');
    if (!res.ok) throw new Error("Server not ok");
    const data = await res.json();
    state.isLiveServer = true;
    if (data.gemini_configured) {
      llmModeText.textContent = "Gemini AI";
      llmEngineTag.textContent = "Gemini 2.5 Flash";
    } else {
      llmModeText.textContent = "Local Engine";
      llmEngineTag.textContent = "Deterministic Symbolic Engine";
    }
  } catch (e) {
    state.isLiveServer = false;
    llmModeText.textContent = "Interactive Mode";
    llmEngineTag.textContent = "Deterministic Benchmark Engine";
  }
}

// 2. Fetch & Render Documents
async function loadDocuments() {
  let docs = [];
  if (state.isLiveServer) {
    try {
      const res = await fetch('/api/documents');
      const data = await res.json();
      docs = data.documents || [];
    } catch (e) {
      state.isLiveServer = false;
      const fallback = CLIENT_FALLBACK_DATA[state.currentDossier] || CLIENT_FALLBACK_DATA.ma_due_diligence;
      docs = fallback.documents;
    }
  } else {
    const fallback = CLIENT_FALLBACK_DATA[state.currentDossier] || CLIENT_FALLBACK_DATA.ma_due_diligence;
    docs = fallback.documents;
  }

  state.documents = docs;
  docCountEl.textContent = docs.length;

  if (docs.length === 0) {
    documentListEl.innerHTML = `<div class="p-4 text-center text-xs text-slate-500">No documents ingested.</div>`;
    return;
  }

  documentListEl.innerHTML = docs.map(doc => `
    <div class="p-2.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 transition group cursor-pointer" onclick="filterByDocument('${doc.doc_id}')">
      <div class="flex items-start justify-between gap-1.5">
        <div class="flex items-center gap-2 truncate">
          <i data-lucide="file-text" class="w-3.5 h-3.5 text-indigo-400 flex-shrink-0"></i>
          <span class="text-xs font-semibold text-slate-200 truncate group-hover:text-indigo-300" title="${doc.doc_name}">${doc.doc_name}</span>
        </div>
        <span class="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700/60 flex-shrink-0">
          ${doc.chunk_count} chunks
        </span>
      </div>
      <div class="mt-1 flex flex-wrap gap-1">
        ${(doc.sections || []).slice(0, 2).map(sec => `
          <span class="text-[9px] text-slate-400 bg-slate-950 px-1.5 py-0.5 rounded border border-slate-800 truncate max-w-[120px]">${sec}</span>
        `).join('')}
        ${(doc.sections || []).length > 2 ? `<span class="text-[9px] text-slate-500">+${doc.sections.length - 2} more</span>` : ''}
      </div>
    </div>
  `).join('');

  refreshIcons();
}

// 3. Load & Render Conflict Matrix
async function loadConflictMatrix() {
  let data = null;
  if (state.isLiveServer) {
    try {
      const res = await fetch('/api/conflict-matrix');
      data = await res.json();
    } catch (e) {
      const fallback = CLIENT_FALLBACK_DATA[state.currentDossier] || CLIENT_FALLBACK_DATA.ma_due_diligence;
      data = fallback.matrix;
    }
  } else {
    const fallback = CLIENT_FALLBACK_DATA[state.currentDossier] || CLIENT_FALLBACK_DATA.ma_due_diligence;
    data = fallback.matrix;
  }

  state.matrixData = data;
  conflictBadgeTotal.textContent = `${data.conflict_count || 0} Conflicts`;

  // Render Matrix Heatmap Table
  const docs = data.document_names || [];
  if (docs.length === 0) {
    matrixTableContainer.innerHTML = `<p class="text-slate-500 py-2">No documents to map.</p>`;
    return;
  }

  let tableHtml = `<table class="w-full text-center border-collapse">`;
  tableHtml += `<thead><tr><th class="p-1 text-slate-500 text-left">Doc</th>`;
  docs.forEach((d, idx) => {
    tableHtml += `<th class="p-1 text-slate-400" title="${d}">D${idx+1}</th>`;
  });
  tableHtml += `</tr></thead><tbody>`;

  docs.forEach((rowDoc, i) => {
    tableHtml += `<tr><td class="p-1 text-left text-slate-400 font-semibold" title="${rowDoc}">D${i+1}</td>`;
    docs.forEach((colDoc, j) => {
      if (i === j) {
        tableHtml += `<td class="p-1 bg-slate-900/40 text-slate-600">-</td>`;
      } else {
        const count = (data.matrix[rowDoc] && data.matrix[rowDoc][colDoc]) || 0;
        if (count > 0) {
          tableHtml += `<td class="p-1 bg-rose-950/70 text-rose-300 font-bold border border-rose-800/40 cursor-pointer hover:bg-rose-900" title="${count} conflict(s) between ${rowDoc} and ${colDoc}">${count}</td>`;
        } else {
          tableHtml += `<td class="p-1 bg-emerald-950/20 text-emerald-400/80 border border-emerald-900/20">0</td>`;
        }
      }
    });
    tableHtml += `</tr>`;
  });
  tableHtml += `</tbody></table>`;
  matrixTableContainer.innerHTML = tableHtml;

  // Render Feed List
  const conflicts = data.conflicts || [];
  if (conflicts.length === 0) {
    conflictFeed.innerHTML = `<div class="p-3 bg-emerald-950/30 border border-emerald-900/50 rounded-lg text-[11px] text-emerald-400">All ingested documents appear mutually compatible. No primary conflicts detected.</div>`;
  } else {
    conflictFeed.innerHTML = conflicts.map(cf => `
      <div class="p-2.5 rounded-lg bg-rose-950/20 border border-rose-900/50 space-y-1 hover:border-rose-700 transition">
        <div class="flex items-center justify-between">
          <span class="text-[10px] font-mono uppercase font-bold text-rose-400">${cf.type.replace('_', ' ')}</span>
          <span class="text-[9px] px-1 rounded bg-rose-900/50 text-rose-300">HIGH SEVERITY</span>
        </div>
        <div class="text-xs font-semibold text-slate-200">${cf.topic}</div>
        <p class="text-[11px] text-slate-400 line-clamp-2">${cf.description}</p>
        <div class="text-[10px] text-indigo-400 font-medium pt-0.5">
          Divergence: ${(cf.involved_documents || []).join(' ⚡ ')}
        </div>
      </div>
    `).join('');
  }

  refreshIcons();
}

// 4. Investigation Execution
investigationForm.addEventListener('submit', (e) => {
  e.preventDefault();
  executeInvestigation();
});

async function executeInvestigation() {
  const query = queryInput.value.trim();
  if (!query) return;

  runInvestigateBtn.disabled = true;
  runInvestigateBtn.innerHTML = `<i data-lucide="loader-2" class="w-3.5 h-3.5 animate-spin"></i> Analyzing...`;
  refreshIcons();

  let result = null;

  if (state.isLiveServer) {
    try {
      const res = await fetch('/api/investigate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query, top_k: 8 })
      });
      result = await res.json();
    } catch (e) {
      state.isLiveServer = false;
      const fallback = CLIENT_FALLBACK_DATA[state.currentDossier] || CLIENT_FALLBACK_DATA.ma_due_diligence;
      result = fallback.default_result;
      result.query = query;
    }
  } else {
    const fallback = CLIENT_FALLBACK_DATA[state.currentDossier] || CLIENT_FALLBACK_DATA.ma_due_diligence;
    result = fallback.default_result;
    result.query = query;
  }

  state.lastInvestigationResult = result;
  renderInvestigationResult(result);

  runInvestigateBtn.disabled = false;
  runInvestigateBtn.innerHTML = `<i data-lucide="crosshair" class="w-3.5 h-3.5"></i> Investigate`;
  refreshIcons();
}

function renderInvestigationResult(result) {
  // 1. Update Certainty Banner
  const cert = result.certainty;
  evidenceSourceCount.textContent = `${result.documents_consulted ? result.documents_consulted.length : 0} Sources`;

  if (cert === "CONFLICT_DETECTED") {
    certaintyBanner.className = "p-4 rounded-xl border flex items-start justify-between gap-4 transition bg-rose-950/40 border-rose-800/80 pulse-conflict";
    certaintyIconContainer.className = "p-2 rounded-lg bg-rose-500/20 text-rose-400 mt-0.5";
    certaintyIconContainer.innerHTML = `<i data-lucide="alert-octagon" class="w-5 h-5"></i>`;
    certaintyTag.className = "px-2 py-0.5 text-xs font-semibold rounded-full bg-rose-900 text-rose-200 border border-rose-700";
    certaintyTag.textContent = "CRITICAL CONTRADICTION DETECTED";
    certaintyHeadline.textContent = "Conflicting assertions found across documents! Do not rely on naive single answers.";
  } else if (cert === "UNVERIFIED_SINGLE_SOURCE") {
    certaintyBanner.className = "p-4 rounded-xl border flex items-start justify-between gap-4 transition bg-amber-950/30 border-amber-800/60";
    certaintyIconContainer.className = "p-2 rounded-lg bg-amber-500/20 text-amber-400 mt-0.5";
    certaintyIconContainer.innerHTML = `<i data-lucide="help-circle" class="w-5 h-5"></i>`;
    certaintyTag.className = "px-2 py-0.5 text-xs font-semibold rounded-full bg-amber-900/60 text-amber-200 border border-amber-700";
    certaintyTag.textContent = "SINGLE SOURCE / UNVERIFIED";
    certaintyHeadline.textContent = "Claim found in only one document. Uncorroborated by independent evidence.";
  } else {
    certaintyBanner.className = "p-4 rounded-xl border flex items-start justify-between gap-4 transition bg-emerald-950/30 border-emerald-800/60";
    certaintyIconContainer.className = "p-2 rounded-lg bg-emerald-500/20 text-emerald-400 mt-0.5";
    certaintyIconContainer.innerHTML = `<i data-lucide="check-circle-2" class="w-5 h-5"></i>`;
    certaintyTag.className = "px-2 py-0.5 text-xs font-semibold rounded-full bg-emerald-900/60 text-emerald-200 border border-emerald-700";
    certaintyTag.textContent = "CROSS-VERIFIED CONSENSUS";
    certaintyHeadline.textContent = "Information is mutually confirmed and corroborated across independent documents.";
  }

  // 2. Discrepancy Box
  const conflicts = (result.conflicts || []).filter(c => c.severity === 'HIGH' || !c.severity);
  if (conflicts.length > 0) {
    discrepancyBox.classList.remove('hidden');
    discrepancyList.innerHTML = conflicts.map((cf, idx) => `
      <div class="p-3 rounded-lg bg-rose-950/30 border border-rose-800/60 flex items-start justify-between gap-3 hover:bg-rose-950/50 transition">
        <div class="space-y-1">
          <div class="flex items-center gap-2">
            <span class="text-xs font-bold text-rose-300">${cf.topic}</span>
            <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-rose-900/80 text-rose-200">${cf.conflict_type}</span>
          </div>
          <p class="text-xs text-slate-300">${cf.description}</p>
          <p class="text-[11px] text-amber-300/90 font-mono">💡 Guidance: ${cf.investigator_advice}</p>
        </div>
        <button onclick="openSideBySideCompare(${idx})" class="px-2.5 py-1.5 bg-rose-900/60 hover:bg-rose-800 text-rose-200 border border-rose-700/60 rounded text-xs font-medium whitespace-nowrap flex items-center gap-1 transition">
          <i data-lucide="split" class="w-3.5 h-3.5"></i> Compare Clauses
        </button>
      </div>
    `).join('');
  } else {
    discrepancyBox.classList.add('hidden');
  }

  // 3. Render Markdown Answer
  if (window.marked) {
    answerMarkdown.innerHTML = window.marked.parse(result.answer || "No response generated.");
  } else {
    answerMarkdown.textContent = result.answer || "No response generated.";
  }

  // 4. Citations
  const citations = result.citations || [];
  citationCount.textContent = `${citations.length} Citations`;
  if (citations.length === 0) {
    citationsGrid.innerHTML = `<p class="text-slate-500 text-xs">No citations captured.</p>`;
  } else {
    citationsGrid.innerHTML = citations.map(cit => `
      <div class="p-3 rounded-lg bg-slate-900/70 border border-slate-800 hover:border-slate-700 transition">
        <div class="flex items-center justify-between text-xs mb-1">
          <span class="font-semibold text-indigo-300 flex items-center gap-1">
            <i data-lucide="file-check" class="w-3.5 h-3.5 text-indigo-400"></i> ${cit.doc_name}
          </span>
          <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
            Page ${cit.page_num} • Section: ${cit.section}
          </span>
        </div>
        <p class="text-xs text-slate-300 font-serif italic border-l-2 border-indigo-500/50 pl-2.5 mt-1.5 leading-relaxed bg-slate-950/40 p-1.5 rounded">
          "${cit.excerpt}"
        </p>
      </div>
    `).join('');
  }

  refreshIcons();
}

// 5. Side-by-Side Clause Comparison Modal
window.openSideBySideCompare = function(conflictIdx) {
  if (!state.lastInvestigationResult) return;
  const conflicts = (state.lastInvestigationResult.conflicts || []).filter(c => c.severity === 'HIGH' || !c.severity);
  const conflict = conflicts[conflictIdx];
  if (!conflict) return;

  compareModalTitle.textContent = `Contradiction: ${conflict.topic}`;
  compareModalSubtitle.textContent = conflict.description;

  const claims = conflict.claims || [];
  if (claims.length < 2) {
    compareModalBody.innerHTML = `<p class="text-slate-400 p-4">Insufficient claims to generate side-by-side view.</p>`;
  } else {
    compareModalBody.innerHTML = claims.slice(0, 2).map((c, i) => `
      <div class="p-4 rounded-xl ${i === 0 ? 'bg-indigo-950/30 border-indigo-800/60' : 'bg-rose-950/30 border-rose-800/60'} border flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-bold ${i === 0 ? 'text-indigo-300' : 'text-rose-300'} flex items-center gap-1.5">
              <i data-lucide="file-text" class="w-3.5 h-3.5"></i> ${c.doc_name}
            </span>
            <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-300">
              Page ${c.page_num} • §${c.section}
            </span>
          </div>
          <div class="mt-2 text-xs font-mono text-slate-400">Asserted Value:</div>
          <div class="text-sm font-bold text-white bg-slate-950/60 p-2 rounded border border-slate-800 my-1">
            ${c.value_raw} (${c.value_type})
          </div>
          <div class="mt-3 text-xs font-mono text-slate-400">Exact Document Quote:</div>
          <blockquote class="text-xs italic text-slate-200 mt-1 p-2.5 rounded bg-slate-950/80 border-l-2 ${i === 0 ? 'border-indigo-500' : 'border-rose-500'}">
            "${c.quote}"
          </blockquote>
        </div>
        <div class="mt-4 pt-2 border-t border-slate-800/60 text-[11px] text-slate-400">
          Source Chunk ID: <code class="text-indigo-400 font-mono text-[10px]">${c.chunk_id}</code>
        </div>
      </div>
    `).join('');
  }

  clauseCompareModal.classList.remove('hidden');
  refreshIcons();
};

closeCompareModalBtn.onclick = () => clauseCompareModal.classList.add('hidden');
closeCompareModalBtn2.onclick = () => clauseCompareModal.classList.add('hidden');

// 6. Benchmark Loading & Chips
const BENCHMARK_METADATA = {
  ma_due_diligence: {
    title: "M&A Acquisition Due Diligence (Project Phoenix)",
    desc: "4 primary documents with conflicting valuation models, closing timelines, and IP liability risks.",
    chips: [
      "What is the agreed purchase price and valuation for Project Phoenix?",
      "What is the scheduled closing date for the acquisition?",
      "Is the core software IP cleanly owned without legal liabilities?"
    ]
  },
  clinical_safety: {
    title: "Clinical Trial CT-904 Safety & Dosage Protocol",
    desc: "Multi-site pharmaceutical trial with diverging dosage recommendations and conflicting safety alerts.",
    chips: [
      "What is the approved daily dosage for study drug CT-904?",
      "Are patients over 65 years of age eligible for the trial?",
      "What is the required frequency for liver enzyme monitoring?"
    ]
  },
  cyber_incident: {
    title: "Cyber Incident Investigation: Breach Response",
    desc: "Conflicting forensic logs, server impact counts, and breach timestamps from SOC vs incident response team.",
    chips: [
      "What was the exact timestamp when the attacker first breached the network?",
      "How many production servers were compromised during the incident?",
      "Was customer personal data (PII) exfiltrated?"
    ]
  }
};

function renderBenchmarkChips() {
  const meta = BENCHMARK_METADATA[state.currentDossier] || BENCHMARK_METADATA.ma_due_diligence;
  activeDossierTitleEl.textContent = meta.title;
  activeDossierDescEl.textContent = meta.desc;

  suggestedChipsEl.innerHTML = meta.chips.map(q => `
    <button onclick="setQuery('${q}')" class="px-2.5 py-1 bg-slate-800/80 hover:bg-indigo-950/60 hover:text-indigo-300 hover:border-indigo-600/50 border border-slate-700/60 rounded-full text-slate-300 text-[11px] whitespace-nowrap transition">
      ${q}
    </button>
  `).join('');
}

window.setQuery = function(q) {
  queryInput.value = q;
  executeInvestigation();
};

loadBenchmarkBtn.onclick = async () => {
  const key = benchmarkSelector.value;
  loadBenchmarkBtn.disabled = true;
  loadBenchmarkBtn.innerHTML = `<i data-lucide="loader-2" class="w-3 h-3 animate-spin"></i>`;
  refreshIcons();

  state.currentDossier = key;
  renderBenchmarkChips();

  if (state.isLiveServer) {
    try {
      await fetch('/api/load-sample', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dossier_key: key })
      });
    } catch (e) {
      console.warn("Server unavailable, switched to client benchmark dataset.");
    }
  }

  await loadDocuments();
  await loadConflictMatrix();

  const meta = BENCHMARK_METADATA[key];
  if (meta && meta.chips.length > 0) {
    queryInput.value = meta.chips[0];
    executeInvestigation();
  }

  loadBenchmarkBtn.disabled = false;
  loadBenchmarkBtn.innerHTML = `<i data-lucide="refresh-cw" class="w-3 h-3"></i> Load`;
  refreshIcons();
};

// 7. Custom Document Upload
openUploadModalBtn.onclick = () => uploadModal.classList.remove('hidden');
closeUploadModalBtn.onclick = () => uploadModal.classList.add('hidden');
cancelUploadBtn.onclick = () => uploadModal.classList.add('hidden');

submitUploadBtn.onclick = async () => {
  const name = document.getElementById('newDocName').value.trim();
  const content = document.getElementById('newDocContent').value.trim();

  if (!name || !content) {
    alert("Please provide both document title and content.");
    return;
  }

  submitUploadBtn.disabled = true;
  if (state.isLiveServer) {
    try {
      await fetch('/api/upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          doc_name: name,
          doc_id: name.toLowerCase().replace(/[^a-z0-9]/g, '_'),
          content: content
        })
      });
      await loadDocuments();
      await loadConflictMatrix();
    } catch (e) {
      console.warn("Live upload error, added locally.");
    }
  } else {
    state.documents.push({
      doc_id: name.toLowerCase().replace(/[^a-z0-9]/g, '_'),
      doc_name: name,
      chunk_count: 2,
      sections: ['Uploaded Clause']
    });
    docCountEl.textContent = state.documents.length;
  }

  uploadModal.classList.add('hidden');
  document.getElementById('newDocName').value = '';
  document.getElementById('newDocContent').value = '';
  executeInvestigation();
  submitUploadBtn.disabled = false;
};

// 8. Configuration Modal (Gemini API Key)
openConfigBtn.onclick = () => configModal.classList.remove('hidden');
closeConfigModalBtn.onclick = () => configModal.classList.add('hidden');
cancelConfigBtn.onclick = () => configModal.classList.add('hidden');

saveConfigBtn.onclick = async () => {
  const key = geminiApiKeyInput.value.trim();
  if (state.isLiveServer) {
    try {
      await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gemini_api_key: key })
      });
    } catch (e) {
      console.warn("Could not save to live backend");
    }
  }
  configModal.classList.add('hidden');
  await fetchHealthAndConfig();
  executeInvestigation();
};

// 9. Export Report Feature
exportReportBtn.onclick = () => {
  if (!state.lastInvestigationResult) {
    alert("No active investigation results to export. Run an investigation first.");
    return;
  }

  const res = state.lastInvestigationResult;
  let markdown = `# Cross-Document Investigation Report\n\n`;
  markdown += `**Investigation Query**: ${res.query}\n`;
  markdown += `**Certainty Status**: ${res.certainty}\n`;
  markdown += `**Engine**: ${res.llm_status}\n\n`;
  markdown += `## Executive Findings\n\n${res.answer}\n\n`;
  markdown += `## Citations & Audit Grounding\n\n`;
  (res.citations || []).forEach((c, idx) => {
    markdown += `### Citation ${idx + 1}: ${c.doc_name}\n`;
    markdown += `- **Page**: ${c.page_num} | **Section**: ${c.section}\n`;
    markdown += `> "${c.excerpt}"\n\n`;
  });

  const blob = new Blob([markdown], { type: 'text/markdown' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `Investigation_Report_${Date.now()}.md`;
  a.click();
  URL.revokeObjectURL(url);
};

// 10. Filter by Document
window.filterByDocument = function(docId) {
  const doc = state.documents.find(d => d.doc_id === docId);
  if (!doc) return;
  queryInput.value = `Summarize key assertions and obligations in ${doc.doc_name}`;
  executeInvestigation();
};
