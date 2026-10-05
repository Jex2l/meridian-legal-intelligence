import pytest

from app.ingestion.extract import extract_docx, extract_pdf


def test_extract_docx(sample_docx):
    result = extract_docx(sample_docx)
    assert len(result.pages) == 1
    assert "MASTER SERVICES AGREEMENT" in result.full_text
    assert "indemnify the Buyer" in result.full_text
    assert result.used_ocr is False


def test_extract_pdf_text_based(sample_pdf):
    result = extract_pdf(sample_pdf)
    assert len(result.pages) == 1
    assert "ARTICLE I" in result.full_text
    assert result.used_ocr is False


def test_extract_pdf_triggers_ocr_path(blank_scanned_pdf, monkeypatch):
    """A page with no extractable text should attempt OCR. We stub the OCR
    function so the test doesn't depend on tesseract/poppler being installed."""
    called = {}

    def fake_ocr(path):
        from app.ingestion.extract import ExtractedPage

        called["yes"] = True
        return [ExtractedPage(page_number=1, text="OCR'd text")]

    monkeypatch.setattr("app.ingestion.extract._ocr_pdf", fake_ocr)
    result = extract_pdf(blank_scanned_pdf)
    assert called.get("yes") is True
    assert result.used_ocr is True
    assert "OCR'd text" in result.full_text
