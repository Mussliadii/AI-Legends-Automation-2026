import streamlit as st
import os
import time
import pandas as pd
import tempfile
from PIL import Image
from google import genai
from extractor import InvoiceExtractor
from validator import InvoiceValidator

st.set_page_config(page_title="AI Legends 2026 - Smart Invoice", page_icon="✨", layout="wide")

# --- CUSTOM CSS ---
custom_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
html, body, [class*="css"] { font-family: 'Outfit', sans-serif !important; }
.stApp { background: radial-gradient(circle at 10% 20%, #1a1a2e 0%, #16213e 50%, #0f3460 100%); color: #ffffff; }
header, footer {visibility: hidden;}

/* Typography */
h1 { font-weight: 800; font-size: 3.5rem; background: -webkit-linear-gradient(45deg, #00f2fe, #4facfe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; line-height: 1.2; margin-bottom: 0px;}
h2 { font-weight: 600; font-size: 2rem; color: #ffffff; margin-top: 30px;}
p.subtitle { text-align: center; color: #a0aabf; font-weight: 300; font-size: 1.3rem; margin-top: 10px; margin-bottom: 50px; max-width: 800px; margin-left: auto; margin-right: auto;}

/* Cards */
.glass-card { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 15px; padding: 25px; margin-bottom: 20px; transition: transform 0.3s ease; }
.glass-card:hover { transform: translateY(-5px); border-color: rgba(79, 172, 254, 0.5); box-shadow: 0 10px 30px 0 rgba(0, 0, 0, 0.4); }

/* Badges */
.badge-AUTO_POST { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: #000; padding: 10px 20px; border-radius: 30px; font-weight: 800; font-size: 1.5rem; text-align: center; display: inline-block; box-shadow: 0 0 15px rgba(56, 239, 125, 0.5); }
.badge-HUMAN_APPROVAL { background: linear-gradient(135deg, #f2994a 0%, #f2c94c 100%); color: #000; padding: 10px 20px; border-radius: 30px; font-weight: 800; font-size: 1.5rem; text-align: center; display: inline-block; box-shadow: 0 0 15px rgba(242, 201, 76, 0.5); }
.badge-DENY { background: linear-gradient(135deg, #cb2d3e 0%, #ef473a 100%); color: #fff; padding: 10px 20px; border-radius: 30px; font-weight: 800; font-size: 1.5rem; text-align: center; display: inline-block; box-shadow: 0 0 15px rgba(239, 71, 58, 0.5); }

/* Data Labels */
.data-label { color: #4facfe; font-size: 0.9rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;}
.data-value { font-size: 1.4rem; font-weight: 400; margin-bottom: 15px; color: #fff;}

/* Grid / Feature Boxes */
.feature-box { background: rgba(0, 0, 0, 0.3); border-radius: 12px; padding: 20px; text-align: center; border: 1px solid rgba(255,255,255,0.05); height: 100%;}
.feature-icon { font-size: 3rem; margin-bottom: 10px; display: block; }
.feature-title { font-weight: 600; font-size: 1.2rem; color: #4facfe; margin-bottom: 10px;}
.feature-desc { font-size: 0.95rem; color: #a0aabf; line-height: 1.5;}

/* Tabs */
.stTabs [data-baseweb="tab-list"] { background-color: rgba(0,0,0,0.3); border-radius: 10px; padding: 5px; gap: 10px;}
.stTabs [data-baseweb="tab"] { color: white; font-weight: 600; font-size: 1.1rem; padding: 10px 20px;}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- INIT AGENT ---
API_KEY = "AIzaSyBM_o2jhPrSPefiPbx3v37Uav16w6ldbFI"
DB_PATH = os.path.join("Data", "master_invoices_database.db")

@st.cache_resource
def load_agents():
    return InvoiceExtractor(api_key=API_KEY), InvoiceValidator(db_path=DB_PATH)

extractor, validator = load_agents()

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135673.png", width=80)
    st.markdown("## System Info")
    st.markdown("**Version:** 1.0.0 (Release)")
    st.markdown("**Core Engine:** Gemini 2.5 Flash")
    st.markdown("**Database:** SQLite (Fuzzy Matching enabled)")
    st.markdown("---")
    st.markdown("### Quick Stats")
    st.metric(label="System Uptime", value="99.9%", delta="Stable")
    st.metric(label="Validation Rules", value="5 Rules", delta="+2 Strict")
    st.markdown("---")
    st.markdown("<p style='font-size:0.8rem; color:#888;'>Built for AI Legends 2026</p>", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("<h1>✨ AI Legends: Smart Invoice Agent</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>The Ultimate Multimodal AI Automation Platform for Extracting, Validating, Classifying, and Chatting with Financial Invoices.</p>", unsafe_allow_html=True)

# --- TABS ---
tab_home, tab_process, tab_qa = st.tabs(["🏠 Home", "📄 Process Document", "💬 Analytics Q&A"])

# ==========================================
# TAB 1: HOME (LANDING PAGE)
# ==========================================
with tab_home:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h2>Welcome to the Future of Finance 🚀</h2>", unsafe_allow_html=True)
    st.markdown("""
        <p style='color:#a0aabf; font-size: 1.1rem; line-height: 1.6;'>
        Manual invoice processing is slow, error-prone, and costs companies millions. Our <b>Smart Invoice Agent</b> revolutionizes this workflow. 
        Simply drop an image or PDF, and our state-of-the-art AI will instantly read, validate against the master database, categorize expenses, and make deterministic business decisions with zero human intervention.
        </p>
    """, unsafe_allow_html=True)
    
    st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin: 30px 0;'>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:#fff; margin-bottom: 25px;'>How It Works</h3>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        <div class='feature-box'>
            <span class='feature-icon'>👁️</span>
            <div class='feature-title'>1. Multimodal Vision</div>
            <div class='feature-desc'>Handles both digital PDFs and mobile-captured images (JPG/PNG) using Gemini 2.5 Flash API. No legacy OCR needed.</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class='feature-box'>
            <span class='feature-icon'>🧠</span>
            <div class='feature-title'>2. Fuzzy Validation</div>
            <div class='feature-desc'>Cross-checks extracted data with our SQLite Master Database. Detects mismatched amounts, duplicate invoices, and unregistered vendors.</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class='feature-box'>
            <span class='feature-icon'>⚖️</span>
            <div class='feature-title'>3. Business Routing</div>
            <div class='feature-desc'>Automatically routes invoices to <b>AUTO_POST</b>, <b>HUMAN_APPROVAL</b>, or <b>DENY</b> based on rigid financial rules.</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown("""
        <div class='feature-box'>
            <span class='feature-icon'>📊</span>
            <div class='feature-title'>4. Aggregate Q&A</div>
            <div class='feature-desc'>Chat natively with your historical invoice data. Ask complex aggregate questions and get instant insights.</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# TAB 2: PROCESS DOCUMENT
# ==========================================
with tab_process:
    uploaded_file = st.file_uploader("Upload an Invoice (Image / PDF format supported)", type=["pdf", "png", "jpg", "jpeg"])
    
    if uploaded_file:
        col_preview, col_result = st.columns([1, 1.2])
        
        with col_preview:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.markdown("<h3 style='margin-top:0; color:#fff;'>🖼️ Document Preview</h3>", unsafe_allow_html=True)
            try:
                if uploaded_file.name.lower().endswith("pdf"):
                    import fitz
                    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                    pix = doc.load_page(0).get_pixmap(dpi=100)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    st.image(img, use_container_width=True, caption=uploaded_file.name)
                else:
                    st.image(uploaded_file, use_container_width=True, caption=uploaded_file.name)
                uploaded_file.seek(0)
            except:
                st.warning("Preview not available for this file.")
            st.markdown("</div>", unsafe_allow_html=True)

        with col_result:
            with st.spinner("🤖 Analyzing Document with Vision AI..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix="."+uploaded_file.name.split('.')[-1]) as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    tmp_path = tmp_file.name
                
                try:
                    start_time = time.time()
                    ext_data = extractor.extract(tmp_path)
                    val_result = validator.validate(ext_data)
                    ptime = time.time() - start_time
                    
                    # Agent Decision Panel
                    st.markdown("<div class='glass-card' style='text-align: center;'>", unsafe_allow_html=True)
                    st.markdown("<p style='color:#a0aabf; font-size:1.1rem; margin-bottom:10px; text-transform:uppercase; font-weight:600;'>Agent Final Decision</p>", unsafe_allow_html=True)
                    decision = val_result['decision']
                    st.markdown(f"<div class='badge-{decision}'>{decision.replace('_', ' ')}</div>", unsafe_allow_html=True)
                    st.markdown(f"<p style='margin-top:15px; font-size:0.95rem; color:#4facfe;'>⚡ AI Processing Time: {ptime:.2f} seconds</p>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                    if val_result['errors']: st.error("❌ REJECTION REASONS:\n\n" + "\n\n".join(val_result['errors']))
                    if val_result['warnings']: st.warning("⚠️ WARNINGS:\n\n" + "\n\n".join(val_result['warnings']))

                    # Extracted Data Details
                    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                    st.markdown("<h3 style='margin-top:0; color:#fff;'>📊 Structured Intelligence</h3>", unsafe_allow_html=True)
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("<div class='data-label'>Vendor Name</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='data-value'>{ext_data.vendor_name}</div>", unsafe_allow_html=True)
                        st.markdown("<div class='data-label'>Financial Category</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='data-value'>{ext_data.category}</div>", unsafe_allow_html=True)
                        st.markdown("<div class='data-label'>Bank Account</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='data-value'>{ext_data.bank_account or '-'}</div>", unsafe_allow_html=True)
                    with c2:
                        st.markdown("<div class='data-label'>Invoice Date</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='data-value'>{ext_data.invoice_date}</div>", unsafe_allow_html=True)
                        st.markdown("<div class='data-label'>Grand Total</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='data-value'>₮ {ext_data.grand_total:,.2f}</div>", unsafe_allow_html=True)
                        st.markdown("<div class='data-label'>Invoice ID</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='data-value'>{ext_data.invoice_number or '-'}</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"Error processing document: {e}")
                finally:
                    os.remove(tmp_path)

# ==========================================
# TAB 3: AGGREGATE Q&A
# ==========================================
with tab_qa:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h3 style='color:#fff;'>💬 Chat with Historical Data</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color:#a0aabf;'>Ask the Large Language Model any question regarding the overall batch processing results. It acts as your personal financial analyst.</p>", unsafe_allow_html=True)
    
    csv_path = os.path.join("output", "batch_results.csv")
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        with st.expander("🔍 View Database (batch_results.csv)"):
            st.dataframe(df, use_container_width=True)
            
        user_q = st.text_input("Ask a question (e.g., 'How many invoices were denied?', 'What are the warnings for invoice 005?'):", placeholder="Type your question here...")
        
        if st.button("Ask Analyst 🤖", use_container_width=True):
            if user_q:
                with st.spinner("Analyzing data and generating answer..."):
                    client = genai.Client(api_key=API_KEY)
                    prompt = f"Here is the result of an invoice automation batch run in CSV format:\n\n{df.to_csv(index=False)}\n\nAnswer the following question clearly, concisely, and professionally: {user_q}"
                    try:
                        resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                        st.markdown("<div style='background:rgba(79, 172, 254, 0.1); padding:20px; border-left: 4px solid #4facfe; border-radius:5px;'>", unsafe_allow_html=True)
                        st.markdown(resp.text)
                        st.markdown("</div>", unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"API Error: {e}")
            else:
                st.warning("Please enter a question.")
    else:
        st.warning("No historical CSV data found. Please run `pipeline.py` first to generate batch results.")
    st.markdown("</div>", unsafe_allow_html=True)
