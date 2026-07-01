import sys

path = "scripts/02d_extract_pdf.py"
src = open(path, encoding="utf-8").read()

old = '''def _docling_to_text(pdf_path):
    from docling.document_converter import DocumentConverter
    converter = DocumentConverter()
    result = converter.convert(str(pdf_path))
    return result.document.export_to_markdown()'''

new = '''def _docling_to_text(pdf_path):
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.datamodel.base_models import InputFormat
    # OCR disabled: these are born-digital publisher PDFs with a real text layer.
    # Docling reads the text directly. Turning OCR off avoids the RapidOCR engine
    # (broken on this install) and gives cleaner, faster extraction.
    opts = PdfPipelineOptions()
    opts.do_ocr = False
    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)}
    )
    result = converter.convert(str(pdf_path))
    return result.document.export_to_markdown()'''

if old not in src:
    print("PATCH TARGET NOT FOUND - the function body differs from expected.")
    print("Paste the current _docling_to_text back to Claude.")
    sys.exit(1)

src = src.replace(old, new)
open(path, "w", encoding="utf-8").write(src)
print("PATCH APPLIED. Verifying:", "do_ocr = False" in open(path, encoding="utf-8").read())