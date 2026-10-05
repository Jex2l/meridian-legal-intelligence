from app.ingestion.chunking import chunk_document
from app.ingestion.extract import extract_docx, extract_pdf


def test_chunk_docx_by_heading(sample_docx):
    extracted = extract_docx(sample_docx)
    chunks = chunk_document(extracted)

    headings = [c.section_heading for c in chunks]
    assert "1. Definitions" in headings
    assert "2. Indemnification" in headings
    assert "(a) Scope" in headings

    scope_chunk = next(c for c in chunks if c.section_heading == "(a) Scope")
    indemnification_chunk = next(c for c in chunks if c.section_heading == "2. Indemnification")
    assert scope_chunk.parent_index == indemnification_chunk.chunk_index


def test_chunk_pdf_tracks_page_numbers(sample_pdf):
    extracted = extract_pdf(sample_pdf)
    chunks = chunk_document(extracted)
    assert all(c.page_number == 1 for c in chunks)
    purpose = next(c for c in chunks if c.section_heading and "Purpose" in c.section_heading)
    assert "key terms of the proposed transaction" in purpose.text


def test_fallback_chunking_without_headings():
    from app.ingestion.extract import ExtractedDocument, ExtractedPage

    doc = ExtractedDocument(pages=[ExtractedPage(page_number=1, text="Just a plain paragraph with no structure.")])
    chunks = chunk_document(doc)
    assert len(chunks) == 1
    assert chunks[0].section_heading is None
