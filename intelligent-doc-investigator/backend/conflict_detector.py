"""
Conflict and Contradiction Detection Engine.
Performs cross-document claim extraction, pairwise claim alignment,
and discrepancy detection (numerical, temporal, polarity, and categorical).
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict
from .document_processor import DocumentChunk

class Claim:
    """Represents an extracted factual claim with exact grounding."""
    def __init__(
        self,
        doc_id: str,
        doc_name: str,
        chunk_id: str,
        section: str,
        page_num: int,
        quote: str,
        topic: str,
        value_raw: str,
        value_type: str,  # 'numeric', 'currency', 'date', 'percentage', 'status', 'text'
        normalized_value: Any,
        polarity: bool = True  # True = affirmative, False = negated
    ):
        self.doc_id = doc_id
        self.doc_name = doc_name
        self.chunk_id = chunk_id
        self.section = section
        self.page_num = page_num
        self.quote = quote
        self.topic = topic
        self.value_raw = value_raw
        self.value_type = value_type
        self.normalized_value = normalized_value
        self.polarity = polarity

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "doc_name": self.doc_name,
            "chunk_id": self.chunk_id,
            "section": self.section,
            "page_num": self.page_num,
            "quote": self.quote,
            "topic": self.topic,
            "value_raw": self.value_raw,
            "value_type": self.value_type,
            "normalized_value": str(self.normalized_value),
            "polarity": self.polarity
        }


class ConflictReport:
    """Represents a detected conflict or consensus finding across documents."""
    def __init__(
        self,
        topic: str,
        conflict_type: str,  # 'NUMERICAL_MISMATCH', 'TEMPORAL_MISMATCH', 'POLARITY_CONTRADICTION', 'CONSENSUS', 'SINGLE_SOURCE'
        severity: str,       # 'HIGH', 'MEDIUM', 'INFO'
        description: str,
        claims: List[Claim],
        investigator_advice: str
    ):
        self.topic = topic
        self.conflict_type = conflict_type
        self.severity = severity
        self.description = description
        self.claims = claims
        self.investigator_advice = investigator_advice

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "conflict_type": self.conflict_type,
            "severity": self.severity,
            "description": self.description,
            "claims": [c.to_dict() for c in self.claims],
            "investigator_advice": self.investigator_advice
        }


class ConflictDetector:
    """Core logic to identify contradictions and discrepancies across multi-document chunks."""

    def __init__(self):
        # Patterns for currency ($50M, $10,000, 50 million dollars, etc.)
        self.currency_pattern = re.compile(
            r'(\$|USD|EUR|GBP|Rs\.?|INR)?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?|\d+)\s*(k|m|b|million|billion|thousand|crore|lakh)?(?:\s*(?:dollars|usd))?',
            re.IGNORECASE
        )
        # Percentage pattern (15%, 99.9%, etc.)
        self.percent_pattern = re.compile(r'([0-9]+(?:\.[0-9]+)?)\s*%', re.IGNORECASE)
        # Date patterns (October 15, 2026; 2026-10-15; 15/10/2026; Q3 2026)
        self.date_pattern = re.compile(
            r'(\b(?:january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}|\b\d{4}-\d{2}-\d{2}|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\bQ[1-4]\s+\d{4})',
            re.IGNORECASE
        )
        # Polarity / Negation triggers
        self.negation_pattern = re.compile(
            r'\b(not|never|no|neither|none|without|prohibited|rejected|denied|excluded|unauthorized|failed|disallowed|cancelled)\b',
            re.IGNORECASE
        )

    def extract_claims_from_chunk(self, chunk: DocumentChunk) -> List[Claim]:
        """Extracts candidate factual assertions (numeric, dates, statuses, metrics) from a chunk."""
        claims = []
        sentences = re.split(r'(?<=[.!?])\s+', chunk.content)

        for sent in sentences:
            sent_clean = sent.strip()
            if len(sent_clean) < 15:
                continue

            is_negated = bool(self.negation_pattern.search(sent_clean))

            # 1. Look for Currencies
            for match in self.currency_pattern.finditer(sent_clean):
                sym, num_str, mult = match.groups()
                # filter out trivial isolated numbers that aren't financial
                if not sym and not mult:
                    continue
                try:
                    clean_num = float(num_str.replace(',', ''))
                    mult_lower = (mult or '').lower()
                    if mult_lower in ['k', 'thousand']:
                        clean_num *= 1000
                    elif mult_lower in ['m', 'million']:
                        clean_num *= 1_000_000
                    elif mult_lower in ['b', 'billion']:
                        clean_num *= 1_000_000_000
                    elif mult_lower in ['crore']:
                        clean_num *= 10_000_000
                    elif mult_lower in ['lakh']:
                        clean_num *= 100_000

                    topic = self._infer_topic(sent_clean, default="Financial Valuation / Cost")
                    claims.append(Claim(
                        doc_id=chunk.doc_id,
                        doc_name=chunk.doc_name,
                        chunk_id=chunk.chunk_id,
                        section=chunk.section,
                        page_num=chunk.page_num,
                        quote=sent_clean,
                        topic=topic,
                        value_raw=match.group(0).strip(),
                        value_type='currency',
                        normalized_value=clean_num,
                        polarity=not is_negated
                    ))
                except ValueError:
                    pass

            # 2. Look for Dates & Deadlines
            for match in self.date_pattern.finditer(sent_clean):
                date_str = match.group(1).strip()
                topic = self._infer_topic(sent_clean, default="Timeline / Milestone Date")
                claims.append(Claim(
                    doc_id=chunk.doc_id,
                    doc_name=chunk.doc_name,
                    chunk_id=chunk.chunk_id,
                    section=chunk.section,
                    page_num=chunk.page_num,
                    quote=sent_clean,
                    topic=topic,
                    value_raw=date_str,
                    value_type='date',
                    normalized_value=date_str.lower(),
                    polarity=not is_negated
                ))

            # 3. Look for Percentages / Metrics
            for match in self.percent_pattern.finditer(sent_clean):
                pct_val = float(match.group(1))
                topic = self._infer_topic(sent_clean, default="Performance / Percentage Metric")
                claims.append(Claim(
                    doc_id=chunk.doc_id,
                    doc_name=chunk.doc_name,
                    chunk_id=chunk.chunk_id,
                    section=chunk.section,
                    page_num=chunk.page_num,
                    quote=sent_clean,
                    topic=topic,
                    value_raw=match.group(0).strip(),
                    value_type='percentage',
                    normalized_value=pct_val,
                    polarity=not is_negated
                ))

            # 4. Status / Compliance / Polarity claims
            status_match = re.search(r'\b(approved|pending|rejected|signed|terminated|compliant|non-compliant|breached|resolved|active|inactive)\b', sent_clean, re.IGNORECASE)
            if status_match:
                st = status_match.group(1).lower()
                topic = self._infer_topic(sent_clean, default="Status / Condition")
                claims.append(Claim(
                    doc_id=chunk.doc_id,
                    doc_name=chunk.doc_name,
                    chunk_id=chunk.chunk_id,
                    section=chunk.section,
                    page_num=chunk.page_num,
                    quote=sent_clean,
                    topic=topic,
                    value_raw=st,
                    value_type='status',
                    normalized_value=st,
                    polarity=not is_negated
                ))

        return claims

    def _infer_topic(self, sentence: str, default: str) -> str:
        """Categorizes the sentence into domain topics to cluster related claims."""
        s = sentence.lower()
        if any(w in s for w in ['valuation', 'purchase price', 'acquisition cost', 'enterprise value', 'equity value']):
            return "Valuation & Purchase Price"
        if any(w in s for w in ['budget', 'spending', 'allocated fund', 'expenditure', 'cap']):
            return "Budget & Expenditure"
        if any(w in s for w in ['closing date', 'closing', 'deadline', 'effective date', 'termination date', 'expiration']):
            return "Closing & Execution Date"
        if any(w in s for w in ['uptime', 'sla', 'availability', 'downtime', 'latency']):
            return "SLA & Uptime Guarantees"
        if any(w in s for w in ['breach', 'incident', 'unauthorized access', 'compromised', 'ransomware', 'servers affected']):
            return "Security Incident Scope"
        if any(w in s for w in ['dosage', 'dose', 'administration', 'mg/day', 'frequency', 'titration']):
            return "Dosage & Protocol Guidelines"
        if any(w in s for w in ['exclusion', 'inclusion', 'criteria', 'eligibility', 'patient age']):
            return "Patient Eligibility Criteria"
        if any(w in s for w in ['penalty', 'liquidated damages', 'liability', 'indemnity']):
            return "Legal Liability & Penalty"
        return default

    def analyze_cross_document_conflicts(self, retrieved_chunks: List[DocumentChunk], query: str = "") -> List[ConflictReport]:
        """
        Cross-analyzes all retrieved chunks across multiple documents to identify
        factual conflicts, discrepancies, or strong consensus.
        """
        all_claims: List[Claim] = []
        for ch in retrieved_chunks:
            all_claims.extend(self.extract_claims_from_chunk(ch))

        # Group claims by topic
        claims_by_topic: Dict[str, List[Claim]] = defaultdict(list)
        for c in all_claims:
            claims_by_topic[c.topic].append(c)

        conflict_reports: List[ConflictReport] = []

        for topic, claims in claims_by_topic.items():
            # Check how many distinct documents are involved
            distinct_docs = {c.doc_id for c in claims}
            if len(distinct_docs) < 2:
                # Mentioned in only 1 document or repeated within same document
                if len(distinct_docs) == 1:
                    first_claim = claims[0]
                    conflict_reports.append(ConflictReport(
                        topic=topic,
                        conflict_type="SINGLE_SOURCE",
                        severity="INFO",
                        description=f"Topic '{topic}' is asserted by '{first_claim.doc_name}', but not corroborated by other ingested documents.",
                        claims=claims[:2],
                        investigator_advice="Treat as unverified single-source information. Verify against additional source files before making high-stakes decisions."
                    ))
                continue

            # Multi-document topic: check for discrepancies
            conflicts_found = False

            # 1. Compare numeric/currency values across documents
            val_groups: Dict[Any, List[Claim]] = defaultdict(list)
            for c in claims:
                if c.value_type in ['currency', 'percentage']:
                    val_groups[c.normalized_value].append(c)

            if len(val_groups) > 1:
                # Numeric divergence across documents!
                distinct_values_by_doc = defaultdict(set)
                for val, c_list in val_groups.items():
                    for c in c_list:
                        distinct_values_by_doc[c.doc_name].add(c.value_raw)

                # Check if multiple documents disagree
                if len(distinct_values_by_doc) >= 2:
                    conflicts_found = True
                    desc_parts = [f"'{doc}': {', '.join(vals)}" for doc, vals in distinct_values_by_doc.items()]
                    desc = f"Direct numeric discrepancy detected across {len(distinct_values_by_doc)} documents: " + "; ".join(desc_parts)

                    conflict_reports.append(ConflictReport(
                        topic=topic,
                        conflict_type="NUMERICAL_MISMATCH",
                        severity="HIGH",
                        description=desc,
                        claims=claims,
                        investigator_advice="Conflicting figures may indicate different audit dates, amended contracts, or unaligned departments. Review timestamps and official sign-offs."
                    ))

            # 2. Compare Dates
            date_claims = [c for c in claims if c.value_type == 'date']
            distinct_dates_by_doc = defaultdict(set)
            for c in date_claims:
                distinct_dates_by_doc[c.doc_name].add(c.value_raw)

            if len(distinct_dates_by_doc) >= 2:
                all_date_vals = {d for s in distinct_dates_by_doc.values() for d in s}
                if len(all_date_vals) > 1:
                    conflicts_found = True
                    desc_parts = [f"'{doc}': {', '.join(dates)}" for doc, dates in distinct_dates_by_doc.items()]
                    desc = f"Temporal mismatch identified: " + " vs ".join(desc_parts)
                    conflict_reports.append(ConflictReport(
                        topic=topic,
                        conflict_type="TEMPORAL_MISMATCH",
                        severity="HIGH",
                        description=desc,
                        claims=date_claims,
                        investigator_advice="Milestone dates diverge across documents. Check for addenda or meeting amendments that supersede earlier drafts."
                    ))

            # 3. Polarity / Status Negation (e.g. Approved vs Rejected, or Negation presence)
            polarities_by_doc = defaultdict(set)
            for c in claims:
                polarities_by_doc[c.doc_name].add(c.polarity)
                if c.value_type == 'status':
                    polarities_by_doc[c.doc_name].add(c.value_raw.lower())

            # Detect affirmative vs negative across documents
            has_affirmative = any(True in p for p in polarities_by_doc.values())
            has_negative = any(False in p for p in polarities_by_doc.values())
            if has_affirmative and has_negative:
                conflicts_found = True
                conflict_reports.append(ConflictReport(
                    topic=topic,
                    conflict_type="POLARITY_CONTRADICTION",
                    severity="HIGH",
                    description=f"Direct polarity contradiction detected regarding '{topic}'. One document affirms or allows it while another negates or prohibits it.",
                    claims=claims,
                    investigator_advice="Legal or operational hazard: check which document has final governing authority or later execution timestamp."
                ))

            # 4. If no conflict found, but multiple documents corroborate:
            if not conflicts_found:
                corroborating_docs = [c.doc_name for c in claims]
                conflict_reports.append(ConflictReport(
                    topic=topic,
                    conflict_type="CONSENSUS",
                    severity="INFO",
                    description=f"Cross-document consensus confirmed across {len(set(corroborating_docs))} documents: {', '.join(set(corroborating_docs))}.",
                    claims=claims[:3],
                    investigator_advice="High-certainty evidence. Independent documents substantiate this fact without discrepancy."
                ))

        # Sort conflict reports by severity (HIGH first)
        severity_order = {'HIGH': 0, 'MEDIUM': 1, 'INFO': 2}
        conflict_reports.sort(key=lambda r: severity_order.get(r.severity, 3))
        return conflict_reports
