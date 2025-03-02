import google.generativeai as genai
from pdf2image import convert_from_path
import os
from unstructured.partition.pdf import partition_pdf
import logging
# Configure logging
import logging

logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG for full logs
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]  # Ensure logs are printed to console
)

# Set up Google Gemini API
API_KEY = "AIzaSyDyrtuYvD8ODMBes1H_3pnCql01rAzOFlc"  # Replace with your actual API key
genai.configure(api_key=API_KEY)

def extract_text_with_unstructured(pdf_path):
    """Extract text from a PDF using Unstructured library."""
    try:
        logging.info("🔍 Starting text extraction with Unstructured...")
        print("🔍 Extracting text...")  # Debug message

        elements = partition_pdf(pdf_path)  # This might be blocking execution
        text = "\n\n".join([str(element) for element in elements])

        logging.info(f"✅ Extracted text (first 1000 chars): {text[:1000]}")  # Debug preview
        print("✅ Text extraction completed!")  # Debug message
        return text or "No text found."
    except Exception as e:
        logging.error(f"❌ Error during PDF text extraction: {str(e)}")
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
    print("🚀 Script started...")  # Debug message
    logging.info("Starting the script...")  # Logging should also work

    pdf_path = input("Enter the path to the PDF file: ")  # Check if input is working
    print(f"📂 Received input: {pdf_path}")  # Debug message

    logging.info("Starting the script...")

    pdf_path = input("Enter the path to the PDF file: ")

    if not os.path.exists(pdf_path):
        print("Error: File not found!")
        exit(1)

    logging.info(f"Processing file: {pdf_path}")

    # Extract text from PDF using a faster method
    extracted_text = extract_text_with_unstructured(pdf_path)

    if extracted_text.startswith("Error"):
        print("Failed to extract text. Exiting.")
        exit(1)

    # Generate summary
    logging.info("Calling Gemini API for summary...")
    summary = generate_summary_with_gemini(extracted_text)

    # Print and save summary
    print("\n=== Summary ===\n")
    print(summary)

    output_file = "summary.txt"
    with open(output_file, "w") as f:
        f.write(summary)

    logging.info(f"Summary saved to {output_file}")


