import os
from PIL import Image
import json
import google.generativeai as genai
from pdf2image import convert_from_path
from dotenv import load_dotenv

# Configure Google Gemini API
# Load environment variables

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# Function to extract text using Gemini
def extract_text_from_pdf_with_gemini (pdf_or_image_path):
    # Check file extension to determine if it's a PDF or an image
    file_extension = os.path.splitext(pdf_or_image_path)[1].lower()

    # For PDF files
    if file_extension == ".pdf":
        images = convert_from_path(pdf_or_image_path, poppler_path=r"C:\\Users\\HP\\Downloads\\Release-24.08.0-0\\poppler-24.08.0\\Library\\bin")
        if not images:
            return "Error: No pages found in PDF."
        img = images[0]  # Use the first page of the PDF
        
    # For image files (jpg, jpeg, png)
    elif file_extension in [".jpg", ".jpeg", ".png"]:
        img = Image.open(pdf_or_image_path)  # Open the image directly
    else:
        return "Error: Unsupported file type. Only PDF, JPG, JPEG, PNG are supported."
    
    # Use the Gemini model to extract text
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content([img])
    
    return response.text if hasattr(response, 'text') else "No text extracted"

def details_extract(text):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
        You are a smart invoice parser.

        Extract the important financial and vendor-related details from the following invoice text. Include, if available:

        - Invoice number
        - Invoice date
        - Vendor name and address
        - Tax breakdown (CGST, SGST, IGST, TDS, other taxes)
        - Subtotal amount
        - Total tax amount
        - Total amount
        - Currency (if mentioned)
        - Line items (each with description, quantity, unit price, total price)
        - Category (e.g., Travel, Office Supplies, etc.)
        - Classification confidence (a number between 0 and 1)

        Return your response in JSON format. Only include fields that are present.

        Invoice Text:
        {text}
        """

    response = model.generate_content([prompt])
    return response.text if hasattr(response, 'text') else None


def clean_gemini_response(response: str) -> str:
    """
    Cleans markdown code block formatting (like ```json) from Gemini's JSON output.
    """
    lines = response.strip().splitlines()
    lines = [line for line in lines if not line.strip().startswith("```")]
    return "\n".join(lines)

def extract_documents(invoice_data):
    try:
        invoice_text = extract_text_from_pdf_with_gemini(invoice_data)
        invoice_details = details_extract(invoice_text)
        print("Gemini Response:", invoice_details)

        # Clean markdown formatting from Gemini's output
        cleaned_invoice_details = clean_gemini_response(invoice_details)

        try:
            parsed_details = json.loads(cleaned_invoice_details)
        except json.JSONDecodeError as e:
            print("Error parsing JSON from Gemini response:", str(e))
            return {
                "invoice_id": "N/A",
                "extracted_data": {
                    "error": "Invalid JSON format from Gemini",
                    "raw_output": invoice_details
                }
            }

        return {
            "invoice_id": parsed_details.get("Invoice number", "N/A"),
            "extracted_data": parsed_details
        }

    except Exception as e:
        print("Extraction Error:", str(e))
        return {
            "invoice_id": "N/A",
            "extracted_data": {
                "error": f"Unexpected error during extraction: {str(e)}"
            }
        }

    