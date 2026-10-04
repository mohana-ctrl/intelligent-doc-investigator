"""
Document Processing Module for Intelligent Document Investigator.
Handles multi-format ingestion (TXT, Markdown, PDF, CSV, JSON, and OCR text),
structure-aware chunking, section detection, and metadata preservation.
"""

import os
import re
import json
import csv
from typing import List, Dict, Any, Optional

class DocumentChunk:
    """Represents an atomic, cited piece of evidence from a document."""
    def __init__(
        self,
        chunk_id: str,
        doc_id: str,
        doc_name: str,
        content: str,
        section: str = "General",
        page_num: int = 1,
        char_start: int = 0,
        char_end: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.chunk_id = chunk_id
        self.doc_id = doc_id
        self.doc_name = doc_name
        self.content = content.strip()
        self.section = section
        self.page_num = page_num
        self.char_start = char_start
        self.char_end = char_end
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "doc_name": self.doc_name,
            "content": self.content,
            "section": self.section,
            "page_num": self.page_num,
            "char_start": self.char_start,
            "char_end": self.char_end,
            "metadata": self.metadata
        }


class DocumentProcessor:
    """Multi-format parser and structure-aware chunker."""

    def __init__(self, chunk_size: int = 400, chunk_overlap: int = 60):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def process_file(self, file_path: str, doc_id: str, doc_name: Optional[str] = None) -> List[DocumentChunk]:
        """Processes a file on disk into structured, cited chunks."""
        doc_name = doc_name or os.path.basename(file_path)
        ext = os.path.splitext(file_path)[1].lower()

        if ext in ['.txt', '.md', '.markdown', '.rst']:
            return self._process_text_or_markdown(file_path, doc_id, doc_name)
        elif ext == '.pdf':
            return self._process_pdf(file_path, doc_id, doc_name)
        elif ext == '.json':
            return self._process_json(file_path, doc_id, doc_name)
        elif ext == '.csv':
            return self._process_csv(file_path, doc_id, doc_name)
        else:
            return self._process_text_or_markdown(file_path, doc_id, doc_name)

    def process_raw_text(self, text: str, doc_id: str, doc_name: str) -> List[DocumentChunk]:
        """Processes raw string content (e.g. from clipboard or direct upload)."""
        sections = self._split_into_sections(text)
        chunks = []
        chunk_idx = 0

        for section_title, section_text, page_estimate in sections:
            section_chunks = self._chunk_text(section_text, self.chunk_size, self.chunk_overlap)
            for ch in section_chunks:
                chunk_id = f"{doc_id}_c{chunk_idx}"
                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        doc_id=doc_id,
                        doc_name=doc_name,
                        content=ch["text"],
                        section=section_title,
                        page_num=page_estimate,
                        char_start=ch["start"],
                        char_end=ch["end"],
                        metadata={"length": len(ch["text"])}
                    )
                )
                chunk_idx += 1
        return chunks

    def _process_text_or_markdown(self, file_path: str, doc_id: str, doc_name: str) -> List[DocumentChunk]:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                raw_text = f.read()
        except Exception as e:
            raw_text = f"Error reading document {doc_name}: {str(e)}"
        return self.process_raw_text(raw_text, doc_id, doc_name)

    def _process_pdf(self, file_path: str, doc_id: str, doc_name: str) -> List[DocumentChunk]:
        """Extracts text page-by-page from PDF. Uses pypdf if available, or lightweight stream fallback."""
        chunks = []
        chunk_idx = 0
        extracted_pages = []

        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            for idx, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                extracted_pages.append((idx + 1, page_text))
        except ImportError:
            try:
                with open(file_path, 'rb') as f:
                    pdf_bytes = f.read()
                text_matches = re.findall(rb'\(([^\)]{2,})\)[\r\n\s]*Tj', pdf_bytes)
                extracted = " ".join([m.decode('latin-1', errors='ignore') for m in text_matches])
                if not extracted.strip():
                    extracted = f"[PDF file: {doc_name} uploaded. Install 'pypdf' for high-precision vector text extraction.]"
                extracted_pages.append((1, extracted))
            except Exception as e:
                extracted_pages.append((1, f"[Error extracting PDF: {str(e)}]"))

        for page_num, page_content in extracted_pages:
            sections = self._split_into_sections(page_content, default_page=page_num)
            for section_title, section_text, p_num in sections:
                if not section_text.strip():
                    continue
                section_chunks = self._chunk_text(section_text, self.chunk_size, self.chunk_overlap)
                for ch in section_chunks:
                    chunk_id = f"{doc_id}_p{p_num}_c{chunk_idx}"
                    chunks.append(
                        DocumentChunk(
                            chunk_id=chunk_id,
                            doc_id=doc_id,
                            doc_name=doc_name,
                            content=ch["text"],
                            section=section_title,
                            page_num=p_num,
                            char_start=ch["start"],
                            char_end=ch["end"],
                            metadata={"source_format": "pdf"}
                        )
                    )
                    chunk_idx += 1
        return chunks

    def _process_json(self, file_path: str, doc_id: str, doc_name: str) -> List[DocumentChunk]:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                data = json.load(f)
            formatted_text = json.dumps(data, indent=2)
            return self.process_raw_text(formatted_text, doc_id, doc_name)
        except Exception as e:
            return self.process_raw_text(f"Error parsing JSON: {e}", doc_id, doc_name)

    def _process_csv(self, file_path: str, doc_id: str, doc_name: str) -> List[DocumentChunk]:
        lines = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                reader = csv.reader(f)
                headers = next(reader, None)
                if headers:
                    lines.append(f"Columns: {', '.join(headers)}")
                    for row_idx, row in enumerate(reader):
                        row_str = " | ".join([f"{h}: {val}" for h, val in zip(headers, row) if val.strip()])
                        lines.append(f"Row {row_idx + 1}: {row_str}")
                else:
                    lines.append("Empty CSV")
            return self.process_raw_text("\n".join(lines), doc_id, doc_name)
        except Exception as e:
            return self.process_raw_text(f"Error parsing CSV: {e}", doc_id, doc_name)

    def _split_into_sections(self, text: str, default_page: int = 1) -> List[tuple]:
        lines = text.splitlines()
        sections = []
        current_title = "Document Overview"
        current_lines = []
        current_page = default_page

        heading_pattern = re.compile(r'^(#{1,4}\s+|[0-9]+\.[0-9]*\s+|SECTION\s+[0-9A-Z]+|ARTICLE\s+[0-9A-Z]+|[A-Z\s]{4,}:)', re.IGNORECASE)

        for line in lines:
            page_match = re.match(r'^-{2,}\s*Page\s+([0-9]+)\s*-{2,}', line, re.IGNORECASE)
            if page_match:
                if current_lines:
                    sections.append((current_title, "\n".join(current_lines), current_page))
                    current_lines = []
                current_page = int(page_match.group(1))
                continue

            if heading_pattern.match(line.strip()) and len(line.strip()) < 80:
                if current_lines:
                    sections.append((current_title, "\n".join(current_lines), current_page))
                    current_lines = []
                current_title = re.sub(r'^[#\s]+', '', line).strip()
            else:
                current_lines.append(line)

        if current_lines:
            sections.append((current_title, "\n".join(current_lines), current_page))

        if not sections:
            sections = [("General Content", text, default_page)]

        return sections

    def _chunk_text(self, text: str, chunk_size: int, overlap: int) -> List[Dict[str, Any]]:
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
        chunks = []
        curr_chunk = []
        curr_len = 0
        char_counter = 0

        for para in paragraphs:
            para_len = len(para)
            if curr_len + para_len > chunk_size and curr_chunk:
                combined_text = "\n\n".join(curr_chunk)
                chunks.append({
                    "text": combined_text,
                    "start": max(0, char_counter - len(combined_text)),
                    "end": char_counter
                })
                if overlap > 0 and len(curr_chunk[-1]) < overlap:
                    curr_chunk = [curr_chunk[-1]]
                    curr_len = len(curr_chunk[0])
                else:
                    curr_chunk = []
                    curr_len = 0

            curr_chunk.append(para)
            curr_len += para_len
            char_counter += para_len + 2

        if curr_chunk:
            combined_text = "\n\n".join(curr_chunk)
            chunks.append({
                "text": combined_text,
                "start": max(0, char_counter - len(combined_text)),
                "end": char_counter
            })

        return chunks
