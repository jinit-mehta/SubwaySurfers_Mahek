import google.generativeai as genai
import pytesseract
from pdf2image import convert_from_path
import os
import logging
POPPLER_PATH = r"C:/poppler-23.11.0/poppler-24.08.0/Library/bin"

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Set up Google Gemini API
API_KEY = "AIzaSyDyrtuYvD8ODMBes1H_3pnCql01rAzOFlc"  # Replace with your actual API key
genai.configure(api_key=API_KEY)

# Configure Tesseract OCR Path (Windows users must set this)
pytesseract.pytesseract.tesseract_cmd = r"C:/Program Files/Tesseract-OCR/tesseract.exe"

def extract_text_with_ocr(pdf_path):
    """Extracts text from a scanned/image-based PDF using OCR."""
    try:
        images = convert_from_path(pdf_path, poppler_path=POPPLER_PATH)  # Use Poppler for PDF conversion
        text = ""

        for i, img in enumerate(images):
            logging.info(f"Processing page {i+1}/{len(images)}...")
            text += pytesseract.image_to_string(img, config="--psm 6") + "\n\n"

        logging.info("OCR text extraction completed.")
        return text or "No text found."
    except Exception as e:
        logging.error(f"Error during OCR: {str(e)}")
        return "Error extracting text."

def generate_summary_with_gemini(text):
    """Generate a structured financial summary using Google Gemini API."""
    try:
        logging.info("Sending request to Gemini API for summarization...")

        # Limit input text to avoid exceeding API limits
        truncated_text = text[:4000]  # Gemini API handles around 4000 chars well
        model = genai.GenerativeModel("gemini-1.5-pro-latest")
        response = model.generate_content(f"Summarize this financial report:\n\n{truncated_text}")

        if response and hasattr(response, "text"):
            logging.info("Received response from Gemini API.")
            return response.text
        else:
            logging.error("No summary generated.")
            return "No summary generated."

    except genai.types.RateLimitError:
        logging.error("Gemini API rate limit exceeded. Try again later.")
        return "API Error: Rate limit exceeded."
    
    except Exception as e:
        logging.error(f"Unexpected Error: {str(e)}")
        return f"Unexpected error: {str(e)}"

if __name__ == "__main__":
    pdf_path = input("Enter the path to the PDF file: ")

    if not os.path.exists(pdf_path):
        print("Error: File not found!")
        exit(1)

    logging.info(f"Processing file: {pdf_path}")

    # Extract text from PDF using OCR
    extracted_text = extract_text_with_ocr(pdf_path)

    if extracted_text.startswith("Error"):
        print("Failed to extract text. Exiting.")
        exit(1)

    # Generate summary
    summary = generate_summary_with_gemini(extracted_text)

    # Print and save summary
    print("\n=== Summary ===\n")
    print(summary)

    # Save to a file
    output_file = "summary.txt"
    with open(output_file, "w") as f:
        f.write(summary)

    logging.info(f"Summary saved to {output_file}")
