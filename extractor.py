import os
import json
from typing import List, Optional
import fitz  # PyMuPDF
from PIL import Image
import io
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# ---------------------------------------------------------
# 1. Output Schema Definition (Structured Data)
# ---------------------------------------------------------
class LineItem(BaseModel):
    item_name: str = Field(description="Нэр / Name or description of the item/service")
    qty: float = Field(description="Тоо хэмжээ / Quantity of the item")
    unit_price: float = Field(description="Нэгж үнэ / Price per unit")
    total: float = Field(description="Нийт дүн / Total price for this line item")

class InvoiceData(BaseModel):
    invoice_number: Optional[str] = Field(None, description="Нэхэмжлэхийн дугаар / Invoice Number")
    vendor_name: str = Field(description="Нийлүүлэгчийн нэр / Vendor or Company Name")
    invoice_date: str = Field(description="Огноо / Invoice Date (YYYY-MM-DD)")
    due_date: Optional[str] = Field(None, description="Төлөх огноо / Due Date (YYYY-MM-DD)")
    bank_name: Optional[str] = Field(None, description="Банкны нэр / Bank Name")
    bank_account: Optional[str] = Field(None, description="Дансны дугаар / Bank Account Number")
    email: Optional[str] = Field(None, description="Имэйл / Email address")
    grand_total: float = Field(description="Нийт төлөх дүн / Grand Total")
    line_items: List[LineItem] = Field(description="Бараа, үйлчилгээний жагсаалт / List of items")
    category: str = Field(description="Санхүүгийн ангилал / Financial Category. Must be one of: 'Түрээсийн зардал', 'Ашиглалтын зардал', 'Мэдээллийн технологийн зардал', 'Тоног төхөөрөмж', 'Тээвэр, логистик', 'Агуулах, хадгалалт', 'Засвар үйлчилгээ', 'Сургалт, хөгжүүлэлт', 'Даатгал', 'Зөвшөөрөл, лиценз'")

# ---------------------------------------------------------
# 2. Multimodal Extraction Engine (PDF & Image)
# ---------------------------------------------------------
class InvoiceExtractor:
    def __init__(self, api_key: str = None):
        """
        Initializes the Extractor using the Gemini API.
        Ensure GEMINI_API_KEY is set in environment variables if api_key is not provided.
        """
        self.client = genai.Client(api_key=api_key)
        self.model_name = 'gemini-2.5-flash'

    def _convert_pdf_to_image(self, pdf_path: str) -> Image.Image:
        """Converts the first page of a PDF into a PIL Image object."""
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)
        pix = page.get_pixmap(dpi=200) # High resolution for better OCR
        img_data = pix.tobytes("png")
        doc.close()
        return Image.open(io.BytesIO(img_data))

    def _load_image(self, file_path: str) -> Image.Image:
        """Loads a standard image (JPG, PNG)."""
        return Image.open(file_path)

    def extract(self, file_path: str) -> InvoiceData:
        """
        Extracts information from an invoice file (PDF/Image) 
        and returns it as a structured Pydantic object.
        """
        ext = file_path.lower().split('.')[-1]
        if ext == 'pdf':
            image = self._convert_pdf_to_image(file_path)
        elif ext in ['jpg', 'jpeg', 'png']:
            image = self._load_image(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

        prompt = (
            "Analyze the attached invoice document (which is in Mongolian/Cyrillic). "
            "Extract all relevant financial information exactly as it appears. "
            "Make sure numbers are converted to correct float values. "
            "If a field is missing, leave it empty or null. "
            "Categorize the invoice based on the items purchased into one of the allowed categories."
        )

        # 3. Call Gemini API with Structured Output (Retry loop added)
        for attempt in range(3):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=[image, prompt],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=InvoiceData,
                        temperature=0.1,
                    ),
                )
                return InvoiceData.model_validate_json(response.text)
            except Exception as e:
                if "503" in str(e) and attempt < 2:
                    print(f"    [!] API Busy (503). Retrying in 5s... (Attempt {attempt+2}/3)")
                    time.sleep(5)
                    continue
                raise e

# ---------------------------------------------------------
# 3. Execution Block (Testing)
# ---------------------------------------------------------
if __name__ == "__main__":
    import sys
    sample_invoice = os.path.join("Data", "invoice_001.jpg")
    extractor = InvoiceExtractor(api_key="AIzaSyBM_o2jhPrSPefiPbx3v37Uav16w6ldbFI") 
    result = extractor.extract(sample_invoice)
    print(result.model_dump_json(indent=2))
