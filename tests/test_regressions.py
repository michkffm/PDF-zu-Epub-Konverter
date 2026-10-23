"""Security and end-to-end regressions for the desktop conversion pipeline."""

import logging
import time
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pytest
from PIL import Image, ImageDraw, ImageFont
from PyQt6.QtWidgets import QApplication

from pdf_epub_converter.core.epub_builder import EPUBBuilder, EPUBBuildError
from pdf_epub_converter.core.metadata import Metadata
from pdf_epub_converter.core.pdf_extractor import (
    DigitalPDFExtractor,
    PDFExtractionError,
)
from pdf_epub_converter.core.quality_checker import QualityReport
from pdf_epub_converter.workers.conversion_worker import ConversionJob, ConversionWorker
from pdf_epub_converter.workers.ocr_worker import OCRWorker, OCRError
from pdf_epub_converter.gui.main_window import MainWindow
from pdf_epub_converter.utils.logger import setup_logger


def text_pdf(
    path, text="Ordinary text for a readable digital book.", width=600, height=800
):
    """Write a genuine one-page PDF fixture without a production writer dependency."""
    safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    content = f"BT /F1 12 Tf 30 700 Td ({safe}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} {height}] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>".encode(),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(content)} >>\nstream\n".encode() + content + b"\nendstream",
    ]
    result = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(result))
        result.extend(f"{index} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(result)
    result.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        result.extend(f"{offset:010d} 00000 n \n".encode())
    result.extend(
        f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    path.write_bytes(result)
    return path


def worker_for(tmp_path, **settings):
    pdf = text_pdf(tmp_path / "input.pdf")
    return ConversionWorker(
        ConversionJob(pdf, tmp_path / "output.epub", Metadata(title="Book"), **settings)
    )


@pytest.mark.parametrize(
    "literal",
    [
        "<script>alert(1)</script>",
        '<img src="https://example.invalid/pixel" onerror="alert(1)"/>',
        "A & B < C",
        "&lt;script&gt;literal&lt;/script&gt;",
    ],
)
def test_untrusted_text_remains_literal_in_epub(tmp_path, literal):
    builder = EPUBBuilder(Metadata(title="Book"))
    builder.add_chapter("Title", literal)
    output = builder.generate(tmp_path / "safe.epub")
    with ZipFile(output) as archive:
        root = ET.fromstring(archive.read("EPUB/chap_000.xhtml"))
    assert not root.findall(".//{*}script")
    assert not root.findall(".//{*}img")
    assert literal in "".join(root.itertext())


def test_builder_does_not_replace_existing_file(tmp_path):
    output = tmp_path / "existing.epub"
    output.write_bytes(b"original")
    builder = EPUBBuilder(Metadata(title="Book"))
    builder.add_chapter("Title", "Text")
    with pytest.raises(EPUBBuildError):
        builder.generate(output)
    assert output.read_bytes() == b"original"


def test_real_digital_conversion_and_temporary_cleanup(tmp_path):
    worker = worker_for(tmp_path)
    results = []
    worker.result.connect(lambda *result: results.append(result))
    worker.run()
    assert results[-1][1] is True
    assert worker.job.output_epub.is_file()
    assert not worker._work_dir.exists()
    assert not (tmp_path / "input_images").exists()


def test_validation_failure_does_not_publish(tmp_path):
    worker = worker_for(tmp_path)
    report = QualityReport()
    report.add_error("Invalid chapter")
    results = []
    worker.result.connect(lambda *result: results.append(result))
    with patch(
        "pdf_epub_converter.workers.conversion_worker.EPUBValidator.validate",
        return_value=report,
    ):
        worker.run()
    assert results[-1][1] is False
    assert not worker.job.output_epub.exists()
    assert not worker._work_dir.exists()


def test_cancel_is_nonblocking_and_never_reports_success(tmp_path):
    worker = worker_for(tmp_path)
    results = []
    worker.result.connect(lambda *result: results.append(result))
    start = time.monotonic()
    worker.stop()
    assert time.monotonic() - start < 0.5
    worker.run()
    assert results[-1][1] is False
    assert "cancelled" in results[-1][2]
    assert not worker.job.output_epub.exists()


def test_images_are_referenced_in_readable_chapter(tmp_path):
    image = tmp_path / "image.png"
    Image.new("RGB", (30, 30), "blue").save(image)
    builder = EPUBBuilder(Metadata(title="Images"))
    builder.add_chapter("Pictures", "", images={"picture": image})
    with ZipFile(builder.generate(tmp_path / "images.epub")) as archive:
        root = ET.fromstring(archive.read("EPUB/chap_000.xhtml"))
        assert root.find(".//{*}img").get("src") == "images/picture.png"
        assert "EPUB/images/picture.png" in archive.namelist()


def test_ocr_real_scanned_pdf_and_auto_detection(tmp_path):
    try:
        OCRWorker(language="en")
    except OCRError as exc:
        pytest.skip(str(exc))
    image = Image.new("RGB", (1200, 500), "white")
    font = (
        ImageFont.truetype("DejaVuSans.ttf", 48)
        if Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf").exists()
        else ImageFont.load_default(size=48)
    )
    ImageDraw.Draw(image).text(
        (60, 100), "HELLO CONVERSION TEST", fill="black", font=font
    )
    pdf = tmp_path / "scan.pdf"
    image.save(pdf, "PDF", resolution=150)
    worker = ConversionWorker(
        ConversionJob(
            pdf,
            tmp_path / "scan.epub",
            Metadata(title="Scan"),
            auto_ocr=True,
            ocr_language="en",
        )
    )
    results = []
    worker.result.connect(lambda *result: results.append(result))
    worker.run()
    assert results[-1][1] is True, results
    with ZipFile(worker.job.output_epub) as archive:
        text = "".join(ET.fromstring(archive.read("EPUB/chap_000.xhtml")).itertext())
        assert "HELLO" in text.upper()
        pictures = ET.fromstring(archive.read("EPUB/chap_001.xhtml"))
        assert pictures.find(".//{*}img") is not None


def test_renderer_page_selection_and_limits(tmp_path):
    pdf = text_pdf(tmp_path / "input.pdf")
    images = OCRWorker.pdf_to_images(pdf, first_page=0, last_page=0)
    try:
        assert images[0][0] == 0
        assert images[0][1].width > 0
    finally:
        images[0][1].close()
    with pytest.raises(OCRError):
        OCRWorker.pdf_to_images(pdf, first_page=1, last_page=1)
    with pytest.raises(OCRError):
        OCRWorker.pdf_to_images(pdf, dpi=10000)


def test_large_page_is_rejected_before_rendering(tmp_path):
    pdf = text_pdf(tmp_path / "large.pdf", width=100000, height=100000)
    with pytest.raises(OCRError, match="megapixel"):
        OCRWorker.pdf_to_images(pdf, first_page=0, last_page=0)


def test_missing_language_has_actionable_error():
    with (
        patch.object(OCRWorker, "_verify_tesseract"),
        patch("pytesseract.get_languages", return_value=["eng"]),
    ):
        with pytest.raises(OCRError, match="deu.*missing"):
            OCRWorker(language="de")


def test_both_tesseract_paths_have_timeout():
    with (
        patch.object(OCRWorker, "_verify_tesseract"),
        patch("pytesseract.get_languages", return_value=["eng"]),
    ):
        worker = OCRWorker(language="en")
    with (
        patch("pytesseract.image_to_string", return_value="text") as text,
        patch("pytesseract.image_to_data", return_value={}) as data,
    ):
        worker.extract_text_from_image(Image.new("RGB", (20, 20)))
        worker.extract_data_from_image(Image.new("RGB", (20, 20)))
        assert text.call_args.kwargs["timeout"] == 60
        assert data.call_args.kwargs["timeout"] == 60


def test_late_file_logging_is_plain_and_not_duplicated(tmp_path):
    name = "regression.file.log"
    logger = setup_logger(name)
    path = tmp_path / "app.log"
    setup_logger(name, log_file=path)
    setup_logger(name, log_file=path)
    logger.info("Ordinary message")
    assert path.read_text().count("Ordinary message") == 1
    assert "\x1b" not in path.read_text()
    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)


def test_gui_queue_two_files_preserves_metadata_and_existing_output(tmp_path):
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    inputs = [text_pdf(tmp_path / f"input{i}.pdf") for i in range(2)]
    for pdf in inputs:
        window.selected_pdfs.append(pdf)
        window._add_file_to_list(pdf)
    window.file_list_widget.setCurrentRow(0)
    window.title_input.setText("First title")
    window.file_list_widget.setCurrentRow(1)
    window.title_input.setText("Second title")
    window.file_list_widget.setCurrentRow(0)
    assert window.title_input.text() == "First title"
    existing = tmp_path / "input0.epub"
    existing.write_bytes(b"keep")
    with patch(
        "pdf_epub_converter.gui.main_window.QFileDialog.getExistingDirectory",
        return_value=str(tmp_path),
    ):
        window.start_conversion()
    deadline = time.monotonic() + 15
    while window.current_worker is not None and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    assert window.current_worker is None
    assert window.start_btn.isEnabled()
    assert existing.read_bytes() == b"keep"
    assert (tmp_path / "input0 (1).epub").exists()
    assert (tmp_path / "input1.epub").exists()
    assert window.selected_pdfs == []
    window.close()


def test_large_digital_page_without_images_still_converts(tmp_path):
    pdf = text_pdf(tmp_path / "poster.pdf", width=10000, height=10000)
    worker = ConversionWorker(
        ConversionJob(pdf, tmp_path / "poster.epub", Metadata(title="Poster"))
    )
    results = []
    worker.result.connect(lambda *result: results.append(result))
    worker.run()
    assert results[-1][1] is True, results


def test_renderer_timeout_terminates_child(tmp_path):
    from pdf_epub_converter.core.rendering import render_page

    with (
        patch("pdf_epub_converter.core.rendering.subprocess.Popen") as child,
        patch("pdf_epub_converter.core.rendering.time.monotonic", side_effect=[0, 31]),
    ):
        child.return_value.poll.return_value = None
        child.return_value.communicate.return_value = (b"", b"")
        with pytest.raises(TimeoutError, match="30 second"):
            render_page(tmp_path / "input.pdf", 0)
        child.return_value.kill.assert_called_once()


def test_renderer_cancellation_terminates_child(tmp_path):
    from pdf_epub_converter.core.rendering import render_page

    with patch("pdf_epub_converter.core.rendering.subprocess.Popen") as child:
        child.return_value.poll.return_value = None
        child.return_value.communicate.return_value = (b"", b"")
        callback_calls = []

        def cancel():
            callback_calls.append(True)
            if len(callback_calls) > 1:
                raise InterruptedError("Cancelled")

        with pytest.raises(InterruptedError):
            render_page(tmp_path / "input.pdf", 0, check_cancel=cancel)
        child.return_value.kill.assert_called_once()


def test_image_extraction_checks_cancel_between_images(tmp_path):
    from unittest.mock import Mock

    pdf = text_pdf(tmp_path / "input.pdf")
    with DigitalPDFExtractor(pdf) as extractor:
        page = Mock()
        page.width, page.height = 600, 800
        page.images = [dict(x0=0, x1=20, top=0, bottom=20)] * 3
        extractor.pdf.pages[:] = [page]
        cancelled = []

        def check():
            if cancelled:
                raise InterruptedError("Cancelled")

        extractor.check_cancel = check

        def rendered(*args, **kwargs):
            cancelled.append(True)
            return Image.new("RGB", (20, 20))

        with patch(
            "pdf_epub_converter.core.pdf_extractor.render_page", side_effect=rendered
        ) as render:
            with pytest.raises(PDFExtractionError, match="Cancelled"):
                extractor.extract_images(tmp_path / "images")
            assert render.call_count == 1


def test_forced_ocr_keeps_page_numbers_and_order(tmp_path):
    from pdf_epub_converter.workers.ocr_worker import ScannedPDFExtractor

    try:
        OCRWorker(language="en")
    except OCRError as exc:
        pytest.skip(str(exc))
    pages = []
    for word in ["FIRST PAGE", "SECOND PAGE"]:
        page = Image.new("RGB", (1200, 500), "white")
        ImageDraw.Draw(page).text(
            (50, 100), word, fill="black", font=ImageFont.load_default(size=48)
        )
        pages.append(page)
    pdf = tmp_path / "two-scans.pdf"
    pages[0].save(pdf, "PDF", resolution=150, save_all=True, append_images=pages[1:])
    with ScannedPDFExtractor(pdf, language="en") as extractor:
        assert "SECOND" in extractor.extract_text_ocr(page_num=1).upper()
        progress = []
        text = extractor.extract_text_ocr(
            progress_callback=lambda *value: progress.append(value)
        ).upper()
        assert text.index("FIRST") < text.index("SECOND")
        assert progress == [(1, 2), (2, 2)]


def test_cancel_after_build_does_not_publish(tmp_path):
    worker = worker_for(tmp_path)
    results = []
    worker.result.connect(lambda *result: results.append(result))
    with patch.object(worker, "_validate_epub", side_effect=lambda path: worker.stop()):
        worker.run()
    assert results[-1][1] is False
    assert not worker.job.output_epub.exists()
    assert not worker._work_dir.exists()


def test_oversized_input_rejected_before_parsing(tmp_path):
    pdf = tmp_path / "large-input.pdf"
    with pdf.open("wb") as output:
        output.truncate(100 * 1024 * 1024 + 1)
    with pytest.raises(PDFExtractionError, match="100 MiB"):
        DigitalPDFExtractor(pdf)


def test_builder_cleans_partial_file_after_write_failure(tmp_path):
    builder = EPUBBuilder(Metadata(title="Book"))
    builder.add_chapter("Title", "Text")
    output = tmp_path / "partial.epub"

    def fail(file, *args):
        file.write(b"partial")
        raise OSError("Write failed")

    with patch(
        "pdf_epub_converter.core.epub_builder.epub.write_epub", side_effect=fail
    ):
        with pytest.raises(EPUBBuildError, match="Write failed"):
            builder.generate(output)
    assert not output.exists()
