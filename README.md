# 🏆 AI Legends 2026: Smart Invoice Automation Agent

![AI Legends Banner](https://img.shields.io/badge/Competition-AI%20Legends%202026-blueviolet?style=for-the-badge)
![Python Version](https://img.shields.io/badge/Python-3.9+-blue?style=for-the-badge&logo=python)
![Framework](https://img.shields.io/badge/Framework-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit)
![AI Model](https://img.shields.io/badge/AI%20Model-Gemini%202.5%20Flash-4285F4?style=for-the-badge&logo=google-gemini)

## 🌟 Overview
**Smart Invoice Agent** is an end-to-end automated solution for processing financial invoices. It leverages state-of-the-art **Multimodal Vision AI** to read documents (Images/PDFs) and applies **Deterministic Business Logic** to validate data against a master database. 

This project was built for the **AI Legends 2026** competition to demonstrate how AI Agents can replace legacy OCR workflows with reliable, explainable, and autonomous systems.

---

## 🚀 Core Features
- **👁️ Multimodal Extraction**: Uses Gemini 2.5 Flash to extract 10+ financial fields from digital PDFs and handwritten mobile photos.
- **🧠 Fuzzy Matching Validation**: Automatically reconciles vendor names and bank accounts against a master SQLite database, even with typos.
- **⚖️ Deterministic Decision Engine**: Routes invoices to `AUTO_POST`, `HUMAN_APPROVAL`, or `DENY` based on 5+ business rules (Math mismatch, duplicates, unregistered vendors).
- **📊 Interactive Dashboard**: A premium Streamlit UI with Glassmorphism design for real-time processing and visualization.
- **💬 Aggregate Q&A Agent**: An LLM-powered analyst that answers complex questions about your entire invoice history.

---

## 🛠️ Technology Stack
- **AI Core**: Google Gemini 2.5 Flash API
- **Backend**: Python 3.11+
- **Frontend**: Streamlit (with Custom CSS Injection)
- **Data Validation**: Pydantic V2, TheFuzz (Levenshtein Distance)
- **Document Processing**: PyMuPDF (fitz), Pillow
- **Database**: SQLite3

---

## 📂 Project Structure
```text
├── Data/                       # Master Database and 100+ Invoice Samples
├── output/                     # Batch results (CSV/JSON)
├── app.py                      # Main Streamlit Web Application
├── extractor.py                # AI Vision Extraction Module
├── validator.py                # Business Logic & Database Validation Module
├── pipeline.py                 # Batch Processing Script
├── submission_notebook.ipynb   # Final Kaggle Competition Notebook
└── Kaggle_Writeup.md           # Professional submission essay
```

---

## ⚙️ Installation & Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/ai-legends-invoice-agent.git
   cd ai-legends-invoice-agent
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: Ensure you have `google-genai`, `pymupdf`, `streamlit`, `pydantic`, `thefuzz`, and `pandas` installed).*

3. **Set API Key**:
   Create a `.env` file or export your Gemini API Key:
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   ```

---

## 🏃 How to Run

### 1. Run the Batch Pipeline
To process all invoices in the `Data/` folder and generate reports:
```bash
python pipeline.py
```

### 2. Launch the Web Dashboard
To start the interactive UI:
```bash
streamlit run app.py
```

---

## 📐 Architecture Workflow
1. **Input**: User uploads a PDF or Image.
2. **Extraction**: Gemini 2.5 Flash extracts structured JSON data.
3. **Validation**: Python Validator checks math, bank details, and historical duplicates.
4. **Decision**: System assigns a routing decision (`AUTO_POST`, etc.).
5. **Analytics**: Results are saved to CSV and become available for the Q&A Agent.

---

## 🏆 Competition Credentials
- **Competition**: AI Legends 2026
- **Track**: AI Agent Automation
- **Author**: [Your Name]

---
*Disclaimer: This tool is a prototype built for demonstration purposes.*
