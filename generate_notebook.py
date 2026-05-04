import nbformat as nbf

# Buat notebook baru
nb = nbf.v4.new_notebook()

# Definisikan sel-sel notebook
cells = []

# 1. Judul & Pendahuluan
cells.append(nbf.v4.new_markdown_cell("""
# 🏆 AI Legends 2026: Smart Invoice Automation Agent
**A Multimodal AI Agent for Extracting, Validating, Classifying, and Chatting with Financial Invoices.**

This notebook contains the complete pipeline for the AI Legends 2026 competition. It utilizes:
1. **Google Gemini 2.5 Flash API** for multimodal vision extraction (No legacy OCR required).
2. **Pydantic** for strict structured JSON outputs.
3. **SQLite & TheFuzz** for historical database validation and fuzzy text matching.
4. **Pandas** for batch processing aggregation.
"""))

# 2. Instalasi Dependensi
cells.append(nbf.v4.new_code_cell("""
# Install required libraries
!pip install -q google-genai pymupdf pillow pydantic thefuzz python-Levenshtein pandas
"""))

# 3. Imports & Config
cells.append(nbf.v4.new_markdown_cell("### 📦 1. Imports and Configuration"))
cells.append(nbf.v4.new_code_cell("""
import os
import json
import glob
import time
import io
import datetime
import sqlite3
import fitz  # PyMuPDF
from PIL import Image
import pandas as pd
from typing import List, Optional, Dict, Any
from thefuzz import fuzz
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# --- Configuration ---
# Note: For Kaggle submission, we use Kaggle Secrets. For local, set the API key here.
API_KEY = "API_KEY" 

# Smart Path detection (Local vs Kaggle)
if os.path.exists("Data"):
    DB_PATH = "Data/master_invoices_database.db"
    DATA_DIR = "Data"
else:
    DB_PATH = "/kaggle/input/ai-legends-data/master_invoices_database.db"
    DATA_DIR = "/kaggle/input/ai-legends-data"

# Create output dir
os.makedirs("output", exist_ok=True)
"""))

# 4. Extractor
cells.append(nbf.v4.new_markdown_cell("### 👁️ 2. Multimodal Extraction Engine (Phase 1)"))
cells.append(nbf.v4.new_code_cell("""
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

class InvoiceExtractor:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model_name = 'gemini-2.5-flash'

    def _convert_pdf_to_image(self, pdf_path: str) -> Image.Image:
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)
        pix = page.get_pixmap(dpi=200)
        img_data = pix.tobytes("png")
        doc.close()
        return Image.open(io.BytesIO(img_data))

    def extract(self, file_path: str) -> InvoiceData:
        ext = file_path.lower().split('.')[-1]
        if ext == 'pdf':
            image = self._convert_pdf_to_image(file_path)
        else:
            image = Image.open(file_path)

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
"""))

# 5. Validator
cells.append(nbf.v4.new_markdown_cell("### 🧠 3. Historical Validation & Logic Engine (Phase 2)"))
cells.append(nbf.v4.new_code_cell("""
class InvoiceValidator:
    def __init__(self, db_path: str):
        self.db_path = db_path
        
    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def validate(self, invoice: InvoiceData) -> Dict[str, Any]:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        errors = []
        warnings = []
        
        # 1. AMOUNT_MISMATCH
        calculated_total = 0
        for item in invoice.line_items:
            expected_line_total = item.qty * item.unit_price
            if abs(expected_line_total - item.total) > 0.01:
                errors.append(f"AMOUNT_MISMATCH: Line item '{item.item_name}' mismatch.")
            calculated_total += item.total
            
        if abs(calculated_total - invoice.grand_total) > 0.01:
            errors.append(f"AMOUNT_MISMATCH: Grand Total mismatch. Calculated: {calculated_total}, On Invoice: {invoice.grand_total}")

        # 2. INVALID_DATE
        try:
            inv_date = datetime.datetime.strptime(invoice.invoice_date, "%Y-%m-%d")
            if invoice.due_date:
                due_date = datetime.datetime.strptime(invoice.due_date, "%Y-%m-%d")
                if due_date < inv_date:
                    errors.append(f"INVALID_DATE: Due date is earlier than invoice date.")
        except ValueError:
            errors.append("INVALID_DATE: Invalid date format (must be YYYY-MM-DD)")

        # 3. UNREGISTERED_VENDOR & BANK_ACCOUNT_MISMATCH
        cursor.execute("SELECT ID, Name, Bank, Account FROM Vendors")
        vendors = cursor.fetchall()
        
        best_match = None
        highest_score = 0
        
        for v in vendors:
            v_id, v_name, v_bank, v_account = v
            score = fuzz.ratio(invoice.vendor_name.lower(), v_name.lower())
            if score > highest_score:
                highest_score = score
                best_match = v
                
        is_vendor_registered = False
        if highest_score < 80:
            warnings.append(f"UNREGISTERED_VENDOR: Vendor '{invoice.vendor_name}' not found.")
        else:
            is_vendor_registered = True
            matched_id, matched_name, matched_bank, matched_account = best_match
            
            if invoice.bank_account:
                inv_acc_clean = invoice.bank_account.replace(" ", "").replace("-", "")
                db_acc_clean = matched_account.replace(" ", "").replace("-", "")
                
                if inv_acc_clean != db_acc_clean:
                    errors.append(f"BANK_ACCOUNT_MISMATCH: Account does not match DB record.")

        # 4. DUPLICATE
        if is_vendor_registered:
            cursor.execute('''
                SELECT InvoiceDate, GrandTotal FROM Invoices 
                WHERE VendorName = ? AND GrandTotal = ?
            ''', (matched_name, invoice.grand_total))
            history = cursor.fetchall()
            
            for h_date_str, h_total in history:
                try:
                    h_date = datetime.datetime.strptime(h_date_str, "%Y-%m-%d")
                    if abs((inv_date - h_date).days) <= 2:
                        errors.append(f"DUPLICATE: Possible duplicate of invoice dated {h_date_str}")
                        break
                except ValueError:
                    continue

        conn.close()

        # 5. FINAL BUSINESS DECISION
        if len(errors) > 0:
            decision = "DENY"
        elif len(warnings) > 0:
            decision = "HUMAN_APPROVAL"
        else:
            decision = "AUTO_POST"

        return {
            "decision": decision,
            "errors": errors,
            "warnings": warnings,
            "vendor_match": best_match[1] if best_match and highest_score >= 80 else None,
            "vendor_match_score": highest_score
        }
"""))

# 6. Pipeline
cells.append(nbf.v4.new_markdown_cell("### ⚡ 4. Automated Batch Pipeline (Phase 3)"))
cells.append(nbf.v4.new_code_cell("""
def process_all_invoices(data_dir: str, limit: int = None):
    print("=== Starting AI Legends 2026 Pipeline ===")
    extractor = InvoiceExtractor(api_key=API_KEY)
    validator = InvoiceValidator(db_path=DB_PATH)

    all_files = []
    for ext in ('*.jpg', '*.png', '*.jpeg', '*.pdf'):
        all_files.extend(glob.glob(os.path.join(data_dir, ext)))
    all_files.sort()
    
    if limit:
        all_files = all_files[:limit]

    results = []

    for file_path in all_files:
        filename = os.path.basename(file_path)
        print(f"Processing {filename}...")
        try:
            ext_data = extractor.extract(file_path)
            val_result = validator.validate(ext_data)
            
            record = {
                "file_name": filename,
                "invoice_number": ext_data.invoice_number,
                "vendor_name": ext_data.vendor_name,
                "invoice_date": ext_data.invoice_date,
                "category": ext_data.category,
                "grand_total": ext_data.grand_total,
                "decision": val_result["decision"],
                "errors": "; ".join(val_result["errors"]),
                "warnings": "; ".join(val_result["warnings"])
            }
            results.append(record)
        except Exception as e:
            print(f"Failed to process {filename}: {e}")

    df = pd.DataFrame(results)
    df.to_csv("output/final_results.csv", index=False)
    print("Pipeline Completed! Results saved to output/final_results.csv")
    return df

# Execute (Set limit to None to process all 100 invoices)
# NOTE: We use try-except because in this local script path might not exist
try:
    results_df = process_all_invoices(data_dir=DATA_DIR, limit=5)
    display(results_df.head())
except Exception as e:
    print("Execution bypassed. Ensure DATA_DIR is correct.", e)
"""))

# 7. Visualization & Insights
cells.append(nbf.v4.new_markdown_cell("### 📊 5. Visual Insights\nGenerating charts to provide a quick overview of the processed batch."))
cells.append(nbf.v4.new_code_cell("""
import matplotlib.pyplot as plt
import seaborn as sns

if 'results_df' in locals() and not results_df.empty:
    # Set style
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(1, 2, figsize=(16, 6))

    # 1. Decision Distribution
    decision_counts = results_df['decision'].value_counts()
    ax[0].pie(decision_counts, labels=decision_counts.index, autopct='%1.1f%%', 
              colors=['#4facfe', '#f2c94c', '#ef473a'], startangle=140)
    ax[0].set_title("Decision Distribution (AUTO_POST vs HUMAN vs DENY)")

    # 2. Category Distribution
    category_counts = results_df['category'].value_counts()
    sns.barplot(x=category_counts.values, y=category_counts.index, ax=ax[1], palette="viridis")
    ax[1].set_title("Invoice Volume by Financial Category")

    plt.tight_layout()
    plt.show()
else:
    print("No data available for visualization.")
"""))

# 8. Conclusion
cells.append(nbf.v4.new_markdown_cell("""
## 🏁 Conclusion
This AI Agent demonstrates a robust approach to financial automation by combining **Multimodal LLMs** with **Deterministic Business Logic**. 
The system is:
- **Scalable**: Can process thousands of documents in batch.
- **Accurate**: Uses fuzzy matching and math validation to catch errors.
- **Explainable**: Provides clear reasons for every decision made.

*Thank you for reviewing our submission for AI Legends 2026!*
"""))

# 9. Aggregate Q&A
cells.append(nbf.v4.new_markdown_cell("### 💬 6. Aggregate Q&A Agent (Phase 4)"))
cells.append(nbf.v4.new_code_cell("""
def ask_analyst(question: str, df: pd.DataFrame):
    client = genai.Client(api_key=API_KEY)
    prompt = f\"\"\"Here is the result of an invoice automation batch run in CSV format:
{df.to_csv(index=False)}
Answer the following question clearly based ONLY on the data provided: {question}\"\"\"
    
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    print("Q:", question)
    print("A:", response.text)
    print("-" * 50)

try:
    if 'results_df' in locals() and not results_df.empty:
        ask_analyst("How many invoices were denied, and what were the main reasons?", results_df)
        ask_analyst("Summarize the total spending by category.", results_df)
except Exception as e:
    print("Q&A execution bypassed.", e)
"""))

nb['cells'] = cells

with open('submission_notebook.ipynb', 'w', encoding='utf-8') as f:
    nbf.write(nb, f)
    
print("submission_notebook.ipynb generated successfully.")
