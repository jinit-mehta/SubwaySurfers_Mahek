from fastapi import FastAPI, File, UploadFile
import PyPDF2
import google.generativeai as genai
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI()
#AIzaSyDyrtuYvD8ODMBes1H_3pnCql01rAzOFlc
# Configure Gemini API
API_KEY = "AIzaSyDyrtuYvD8ODMBes1H_3pnCql01rAzOFlc"
genai.configure(api_key=API_KEY)

@app.post("/summarize/")
async def summarize_pdf(file: UploadFile = File(...)):
    try:
        logging.info(f"Received file: {file.filename}")

        # Save the uploaded file temporarily
        file_path = f"temp_{file.filename}"
        with open(file_path, "wb") as f:
            f.write(await file.read())
        logging.info(f"File saved at: {file_path}")

        # Extract text from PDF
        text = extract_text_from_pdf(file_path)
        logging.info("Text extraction completed.")

        # Send to Gemini API
        summary = generate_summary(text)
        logging.info("Summary generation completed.")

        # Clean up temp file
        os.remove(file_path)
        logging.info(f"Temporary file deleted: {file_path}")

        return {"summary": summary}

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return {"error": str(e)}

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    try:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        
        logging.info(f"Extracted text (first 500 chars): {text[:500]}")  # Print preview
        return text or "No text found."
    except Exception as e:
        logging.error(f"Error extracting text: {str(e)}")
        return "Error extracting text."


# Function to generate summary using Gemini API
def generate_summary(text):
    try:
        logging.info("Sending request to Gemini API for summarization...")
        model = genai.GenerativeModel("gemini-1.5-pro-latest")
        response = model.generate_content(f"Summarize this financial report:\n\n{text}")
        logging.info("Received response from Gemini API.")
        return response.text
    except Exception as e:
        logging.error(f"Gemini API Error: {str(e)}")
        return "Error in generating summary."
