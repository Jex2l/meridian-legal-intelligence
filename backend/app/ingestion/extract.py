"""Text extraction for PDF and DOCX, with OCR fallback for scanned PDFs."""

from dataclasses import dataclass
from pathlib import Path

import pdfplumber
from docx import Document as DocxDocument
from pypdf import PdfReader

MIN_CHARS_PER_PAGE_BEFORE_OCR = 20


@dataclass
class ExtractedPage:
    page_number: int  # 1-indexed
    text: str


@dataclass
class ExtractedDocument:
    pages: list[ExtractedPage]
    used_ocr: bool = False

    @property
    def full_text(self) -> str:
        return "\n\n".join(p.text for p in self.pages)


def extract_pdf(path: Path) -> ExtractedDocument:
    pages: list[ExtractedPage] = []
    try:
        with pdfplumber.open(path) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                pages.append(ExtractedPage(page_number=i, text=text))
    except Exception as exc:  # noqa: BLE001  pdfplumber/pypdf raise several
        # library-specific exception types for a malformed PDF; normalize
        # to one clear message.
        raise ValueError("Could not parse file as PDF -- it may be corrupted or not a real .pdf file") from exc

    needs_ocr = any(len(p.text.strip()) < MIN_CHARS_PER_PAGE_BEFORE_OCR for p in pages)
    if not needs_ocr:
        return ExtractedDocument(pages=pages, used_ocr=False)

    ocr_pages = _ocr_pdf(path)
    merged = []
    for original, ocr in zip(pages, ocr_pages):
        text = original.text if len(original.text.strip()) >= MIN_CHARS_PER_PAGE_BEFORE_OCR else ocr.text
        merged.append(ExtractedPage(page_number=original.page_number, text=text))
    return ExtractedDocument(pages=merged, used_ocr=True)


def _ocr_pdf(path: Path) -> list[ExtractedPage]:
    """OCR fallback for scanned PDFs using pdf2image + pytesseract.

    Imported lazily: these deps (and the poppler/tesseract binaries they
    shell out to) are only needed on the OCR path, so a dev box without
    poppler/tesseract installed can still ingest text-based PDFs.
    """
    import pytesseract
    from pdf2image import convert_from_path

    images = convert_from_path(str(path))
    pages = []
    for i, image in enumerate(images, start=1):
        text = pytesseract.image_to_string(image)
        pages.append(ExtractedPage(page_number=i, text=text))
    return pages


def extract_docx(path: Path) -> ExtractedDocument:
    """DOCX has no native page concept; we treat the whole document as
    page 1 and let chunking split by heading instead of page boundary."""
    try:
        doc = DocxDocument(str(path))
    except Exception as exc:  # noqa: BLE001  python-docx raises various
        # library-internal exception types (zipfile.BadZipFile, its own
        # PackageNotFoundError, etc.) whose messages include the internal
        # temp file path -- normalize to one clear message without it.
        raise ValueError("Could not parse file as DOCX -- it may be corrupted or not a real .docx file") from exc
    lines = [para.text for para in doc.paragraphs]
    text = "\n".join(lines)
    return ExtractedDocument(pages=[ExtractedPage(page_number=1, text=text)], used_ocr=False)


def extract(path: Path) -> ExtractedDocument:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_pdf(path)
    if suffix == ".docx":
        return extract_docx(path)
    raise ValueError(f"Unsupported file type: {suffix}")


def pdf_page_count(path: Path) -> int:
    return len(PdfReader(str(path)).pages)
