import PyPDF2
from io import BytesIO

def extract_text_from_pdf(file_bytes):
    """Extract text from an uploaded PDF file."""
    pdf_reader = PyPDF2.PdfReader(BytesIO(file_bytes))
    text = ""
    for page in pdf_reader.pages:
        extracted_text = page.extract_text()
        if extracted_text:
            text += extracted_text + "\n"
    return text
    