"""
Pre-packaged realistic investigation dossiers for Algothon'26 demonstrations.
Features deliberate cross-document contradictions (numerical, temporal, polarity, and categorical).
"""

from typing import Dict, List

SAMPLE_DOSSIERS = {
    "ma_due_diligence": {
        "title": "M&A Acquisition Due Diligence (Project Phoenix)",
        "description": "High-stakes corporate buyout with conflicting valuations, conflicting closing dates, and contradictory IP warranties.",
        "suggested_queries": [
            "What is the agreed purchase price and valuation for Project Phoenix?",
            "What is the scheduled closing date for the acquisition?",
            "Is the core software IP cleanly owned without legal liabilities?"
        ],
        "documents": [
            {
                "id": "phoenix_cim",
                "name": "Project_Phoenix_Confidential_Memorandum.md",
                "content": """# Project Phoenix: Confidential Information Memorandum
Date: September 1, 2026
Prepared By: Global Tech Advisory Group

## 1. Executive Summary
Project Phoenix represents the acquisition of CloudSync Corp, an enterprise SaaS leader.
The enterprise valuation agreed upon for this transaction is $50,000,000 USD ($50M).
The proposed transaction structure is 80% cash and 20% stock equity.

## 2. Financial Metrics
CloudSync Corp reported Fiscal Year 2025 revenue of $24,500,000 with an adjusted EBITDA of $8,200,000.
Cash reserves on balance sheet stand at $4,500,000. Current annualized recurring revenue (ARR) growth is 35%.

## 3. Timeline & Closing Schedule
Both executive boards have aligned on a definitive closing date of October 15, 2026.
Regulatory antitrust filings were submitted in August 2026 with no objections received.

## 4. Intellectual Property & Codebase
CloudSync Corp confirms that all proprietary algorithms and core platform components are 100% cleanly owned, developed by direct employees under assignment agreements, and free from restrictive third-party open source licenses.
"""
            },
            {
                "id": "phoenix_audit",
                "name": "Independent_Financial_Audit_Report.md",
                "content": """# Independent Financial Due Diligence & Audit
Client: Buy-Side Investment Consortium
Date: September 28, 2026
Auditor: Delmar & Hastings Forensic Accounting

--- Page 1 ---
## SECTION 1: Valuation Restatement
Following forensic inspection of CloudSync Corp's balance sheet, deferred revenues and undisclosed vendor obligations have been identified.
Our revised valuation firmly establishes the fair enterprise valuation at $41,800,000 USD ($41.8M), representing a significant downgrade from the $50,000,000 claimed in the memorandum.

--- Page 2 ---
## SECTION 2: Restated EBITDA & Liabilities
Forensic adjustments reduce the adjusted EBITDA from $8,200,000 down to $5,900,000 due to capitalized R&D expenses that should have been recognized as operational expenses.
Unrecorded cloud hosting debt owed to AWS is verified at $1,250,000.

## SECTION 3: Closing Timeline Considerations
Closing on October 15, 2026 remains theoretically achievable, but our team advises a 30-day escrow withholding to reconcile working capital disputes.
"""
            },
            {
                "id": "phoenix_board",
                "name": "Special_Board_Meeting_Minutes.md",
                "content": """# Confidential Minutes of Special Board of Directors Meeting
Acquiring Entity: Horizon Global Holdings
Date: October 2, 2026

## 1. Attendance & Quorum
Meeting called to order at 14:00 EST. Present: Chairman Vance, CEO Sterling, CFO Rivera, General Counsel Chen.

## 2. Review of Project Phoenix Discrepancies
CFO Rivera presented the Delmar & Hastings forensic findings. The board debated the valuation gap between $50M and $41.8M.
Resolution 4B: The Board voted unanimously NOT to approve any transaction exceeding $44,000,000.
CEO Sterling is instructed to reopen price negotiations immediately.

## 3. Revised Closing Milestone
Given the price impasse and required restructuring, the Board formally moved and approved pushing the definitive closing date from October 15, 2026 to November 30, 2026.
Closing is strictly conditioned on receiving audited clean intellectual property verification.
"""
            },
            {
                "id": "phoenix_legal_ip",
                "name": "Legal_Codebase_IP_Assessment.md",
                "content": """# Legal Due Diligence: Codebase & Intellectual Property Analysis
Law Firm: Sterling & Sterling LLP
Date: October 3, 2026

## SECTION A: Scope of Audit
Static code analysis and dependency auditing of CloudSync's flagship microservices architecture.

## SECTION B: Open Source Licensing Infringements
Contrary to representations in the Confidential Information Memorandum, the core streaming data engine incorporates code licensed under GNU GPL v3.0 without attribution or isolation.
This triggers copyleft obligations, meaning CloudSync's proprietary algorithms are legally vulnerable to open-source release demands.

## SECTION C: IP Ownership Conclusion
Intellectual property is NOT cleanly owned without encumbrance.
Remediation cost to re-architect and rewrite the tainted modules is estimated at $1,800,000 and will require approximately 4 months of engineering effort.
"""
            }
        ]
    },
    "clinical_safety": {
        "title": "Clinical Trial CT-904 Safety & Dosage Protocol",
        "description": "Multi-site pharmaceutical trial with diverging dosage recommendations and conflicting safety alerts.",
        "suggested_queries": [
            "What is the approved daily dosage for study drug CT-904?",
            "Are patients over 65 years of age eligible for the trial?",
            "What is the required frequency for liver enzyme monitoring?"
        ],
        "documents": [
            {
                "id": "clinical_protocol",
                "name": "Clinical_Trial_Protocol_v4.md",
                "content": """# Phase II Clinical Protocol: Investigational Compound CT-904
Protocol Number: CT-904-2026
Principal Sponsor: BioNova Therapeutics

## 1. Dosing Schedule
The therapeutic target dosage is 100 mg/day administered orally in two 50 mg increments.
Dose titration begins on Day 1 with 50 mg/day for 7 days, stepping up to 100 mg/day thereafter.

## 2. Inclusion & Exclusion Criteria
Eligible subjects include adult males and non-pregnant females aged 18 to 75 years diagnosed with moderate inflammatory disease.
Patients aged 65 to 75 are explicitly eligible provided normal renal function is documented.

## 3. Laboratory Monitoring
Safety laboratory blood panels, including ALT and AST liver enzymes, shall be performed monthly (every 30 days) during the 24-week active evaluation period.
"""
            },
            {
                "id": "safety_advisory",
                "name": "Data_Safety_Monitoring_Board_Urgent_Advisory.md",
                "content": """# DSMB Safety Advisory #04: Urgent Protocol Deviation
Date: September 22, 2026
To: All Clinical Investigators and Institutional Review Boards

## 1. Safety Signal Warning: Hepatotoxicity
Following three Grade 3 hepatic enzyme elevation events observed at Trial Site C, the DSMB has ordered an immediate protocol restriction.
Effective immediately, the maximum allowable dosage is reduced from 100 mg/day to 50 mg/day. No patient may receive 100 mg/day under any circumstances.

## 2. Emergency Exclusion Revision
Sub-group analysis revealed that all three adverse hepatic events occurred in subjects aged 65 and older.
Patients over 65 years of age are now strictly excluded from ongoing participation and new enrollment.

## 3. Intensified Liver Monitoring
The monthly monitoring schedule is deemed inadequate. Liver function tests (ALT/AST/Bilirubin) must now be performed weekly for the first 8 weeks of therapy.
"""
            }
        ]
    },
    "cyber_incident": {
        "title": "Cyber Incident Investigation: Breach Response",
        "description": "Conflicting forensic logs, server impact counts, and breach timestamps from SOC vs incident response team.",
        "suggested_queries": [
            "What was the exact timestamp when the attacker first breached the network?",
            "How many production servers were compromised during the incident?",
            "Was customer personal data (PII) exfiltrated?"
        ],
        "documents": [
            {
                "id": "soc_alert_log",
                "name": "SOC_Security_Operations_Incident_Log.md",
                "content": """# SOC Incident Report #IR-8821
Severity: CRITICAL
Classification: Unauthorized Access & Potential Lateral Movement
Date: August 14, 2026

## 1. Detection Timeline
At 03:15:22 UTC on August 14, 2026, an anomaly alert triggered on Perimeter Firewall DMZ-02.
Initial perimeter breach is recorded as August 14, 2026 at 03:15 UTC via compromised VPN credentials.

## 2. Compromised Asset Count
Security telemetry indicates 4 production servers were accessed by the intruder: web-app-01, web-app-02, db-auth-01, and proxy-01.
No cloud storage buckets were queried.

## 3. Data Exfiltration Status
DLP network monitoring registered zero outbound high-volume transfers. Initial assessment: Customer PII was not exfiltrated.
"""
            },
            {
                "id": "external_forensics",
                "name": "Mandiant_External_Forensics_Final_Report.md",
                "content": """# Independent Digital Forensics & Incident Response (DFIR) Report
Investigator: IronClad Cyber Forensics LLC
Date: August 29, 2026

--- Page 1 ---
## SECTION 1: Corrected Root Cause & Initial Ingress Timeline
Deep forensic inspection of memory dumps and NetFlow records reveals that the attacker actually gained initial access on August 11, 2026 at 22:40 UTC—nearly 53 hours earlier than the internal SOC log of August 14 at 03:15 UTC.
Initial entry was achieved via unpatched CVE-2026-4401 on legacy VPN gateway.

--- Page 2 ---
## SECTION 2: True Blast Radius & Compromised Assets
The attacker achieved domain administrator privilege escalation. A total of 19 production servers were compromised, including active database mirrors and directory controllers (contrasting the SOC estimate of 4 servers).

--- Page 3 ---
## SECTION 3: Exfiltration Verification
Contrary to the SOC conclusion, forensics confirmed the exfiltration of 84 Gigabytes of encrypted archive files containing approximately 450,000 customer PII records via DNS tunneling.
"""
            }
        ]
    }
}
