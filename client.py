import streamlit as st
import requests
import json
import time
import os

# --- 1. CONFIG & SECRETS ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    GEMINI_API_KEY = st.secrets["GEMINI_KEY"]
except:
    st.error("⚠️ کلیلەکان نەدۆزرانەوە. تکایە Secrets ڕێکبخە.")
    st.stop()

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# --- 2. UI CONFIGURATION ---
st.set_page_config(page_title="Zirak AI", page_icon="🦁", layout="wide", initial_sidebar_state="expanded")

# --- 3. ADVANCED CSS STYLING (MATCHING SCREENSHOTS) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;700;900&display=swap');
        
        * {
            font-family: 'Vazirmatn', sans-serif;
            box-sizing: border-box;
        }
        
        /* ڕەنگی باکگراوندی گشتی */
        .stApp {
            background-color: #F8F9FA;
        }

        /* --- 1. LOGIN PAGE STYLING --- */
        /* شاردنەوەی سایدبار لە کاتی Login */
        [data-testid="stSidebar"] {
            display: none;
        }
        
        /* کارتەکەی ناوەڕاست */
        .login-container {
            background: white;
            padding: 40px;
            border-radius: 24px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.08);
            text-align: center;
            max-width: 400px;
            margin: 50px auto;
            direction: rtl;
        }
        
        .login-icon {
            font-size: 50px;
            background: linear-gradient(135deg, #FF6600, #FF3366);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        .login-title {
            font-size: 24px;
            font-weight: 900;
            color: #111827;
            margin-bottom: 5px;
        }
        
        .login-subtitle {
            font-size: 14px;
            color: #6B7280;
            margin-bottom: 30px;
        }
        
        /* ئینپوتەکان */
        .stTextInput input {
            background-color: #F3F4F6;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            padding: 10px 15px;
            text-align: right;
            direction: rtl;
            color: #111827;
        }
        
        /* دوگمەی چوونەژوورەوە (ڕەش) */
        .stButton button {
            background-color: #111827 !important;
            color: white !important;
            border-radius: 12px !important;
            padding: 12px 0 !important;
            font-weight: bold !important;
            border: none !important;
            width: 100%;
            transition: all 0.3s;
        }
        .stButton button:hover {
            background-color: #000000 !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }

        /* --- 2. SIDEBAR STYLING (Dark Blue) --- */
        section[data-testid="stSidebar"] {
            display: block !important; /* پیشاندانی سایدبار دوای چوونەژوورەوە */
            background-color: #0F172A !important; /* Dark Blue */
            color: white !important;
        }
        
        section[data-testid="stSidebar"] h1, 
        section[data-testid="stSidebar"] h2, 
        section[data-testid="stSidebar"] h3, 
        section[data-testid="stSidebar"] p, 
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] div {
            color: white !important;
        }

        /* ڕادیۆ بەتەنەکان (Menu Items) */
        .stRadio label {
            color: white !important;
            background: transparent;
            padding: 10px;
            border-radius: 8px;
            transition: background 0.3s;
        }
        .stRadio label:hover {
            background: rgba(255,255,255,0.1);
        }

        /* پڕۆگرێس باڕی باڵانس */
        .stProgress > div > div > div > div {
            background-color: #FF6600 !important; /* ڕەنگی نارنجی */
        }

        /* --- 3. MAIN CHAT AREA --- */
        /* هێدەر */
        header[data-testid="stHeader"] {
            background: transparent;
        }

        /* بۆشایی ناوەڕاست (Empty State - Brain Icon) */
        .hero-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 60vh;
            text-align: center;
            color: #9CA3AF;
        }
        
        .hero-icon {
            font-size: 80px;
            color: #A855F7; /* Purple */
            background: #F3E8FF;
            width: 120px;
            height: 120px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 40px;
            margin-bottom: 20px;
        }

        .hero-text {
            font-size: 22px;
            font-weight: bold;
            color: #D1D5DB;
        }
        
        /* Chat Messages */
        .stChatMessage {
            direction: rtl;
            text-align: right;
        }

        /* --- 4. FLOATING BUTTON (Attachment) --- */
        [data-testid="stPopover"] {
            position: fixed !important;
            bottom: 100px !important;
            right: 30px !important;
            z-index: 9999;
            background-color: white !important;
            border-radius: 50% !important;
            width: 50px !important;
            height: 50px !important;
            border: 2px solid #E5E7EB !important;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1) !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        
        [data-testid="stPopover"] button {
            color: #6B7280 !important;
            font-size: 20px !important;
            padding: 0 !important;
            border: none !important;
        }
        
        /* Mobile Adjustments */
        @media only screen and (max-width: 600px) {
            [data-testid="stPopover"] {
                bottom: 90px !important;
                right: 20px !important;
            }
            .login-container {
                margin: 20px;
                padding: 20px;
            }
        }
    </style>
""", unsafe_allow_html=True)

# --- 4. HELPER FUNCTIONS ---
@st.cache_data(ttl=300)
def get_user_data(username):
    try:
        url = f"{SUPABASE_URL}/rest/v1/users?username=eq.{username}&select=*"
        res = requests.get(url, headers=HEADERS)
        return res.json()[0] if res.status_code == 200 and res.json() else None
    except: return None

def update_tokens_db(username, new_total):
    requests.patch(f"{SUPABASE_URL}/rest/v1/users?username=eq.{username}", 
                   headers=HEADERS, json={"used_tokens": new_total})
    get_user_data.clear()

def save_chat(username, role, content, expert):
    requests.post(f"{SUPABASE_URL}/rest/v1/chat_history", headers=HEADERS, 
                  json={"username": username, "role": role, "content": content, "expert": expert})

def get_expert_prompt(expert_name):
    # مێشکی پسپۆڕەکان
    prompts = {
        "🧠 مێشکی کۆرسەکە": "Role: Course Expert. Answer solely based on the course content.",
        "🗣️ وەرگێڕی بازرگانی": "Role: Professional Translator (Kurdish/English). Formal tone.",
        "📐 حاسیبەی لۆجستی": "Role: Logistics Calculator. Calculate CBM and Volumetric weight accurately.",
        "✍️ ستراتیژیستی ناوەڕۆک": "Role: Content Strategist. Creative and viral ideas.",
        "📈 ڕاپۆرتی نهێنی": "Role: Market Analyst. Use provided report data only."
    }
    for key in prompts:
        if key in expert_name: return prompts[key]
    return "Role: Helpful Assistant."

def get_ai_response(prompt, history, expert_prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    contents = []
    for msg in history[-6:]: 
        contents.append({"role": "user" if msg['role'] == "user" else "model", "parts": [{"text": msg['content']}]})
    contents.append({"role": "user", "parts": [{"text": f"Instruction: {expert_prompt}\nInput: {prompt}"}]})
    
    try:
        res = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps({"contents": contents}))
        if res.status_code == 200:
            data = res.json()
            return data['candidates'][0]['content']['parts'][0]['text'], data.get('usageMetadata', {}).get('totalTokenCount', 0)
        return "⚠️ سێرڤەر وەڵامی نییە.", 0
    except: return "🚫 کێشەی تەکنیکی.", 0

# --- 5. MAIN APP ---
def main():
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False

    # --- PART 1: LOGIN PAGE (Custom UI) ---
    if not st.session_state.logged_in:
        # لێرەدا CSSـی تایبەت بە Login کار دەکات
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
                <div class="login-container">
                    <div class="login-icon">🦁</div>
                    <div class="login-title">بەخێربێیتەوە</div>
                    <div class="login-subtitle">تکایە زانیارییەکانت بنووسە</div>
                </div>
            """, unsafe_allow_html=True)
            
            # فۆڕمی چوونەژوورەوە لەناو کۆڵۆمەکە
            with st.form("login_form"):
                u = st.text_input("نازناو")
                p = st.text_input("وشەی نهێنی", type="password")
                submitted = st.form_submit_button("چوونەژوورەوە")
                
                if submitted:
                    user = get_user_data(u.strip())
                    if user and str(user['password']) == str(p.strip()):
                        st.session_state.logged_in = True
                        st.session_state.username = u.strip()
                        st.rerun()
                    else:
                        st.error("زانیاری هەڵەیە")
        return

    # --- PART 2: DASHBOARD (APP MODE) ---
    # گۆڕینی ستایل بۆ دۆخی ئەپ (Sidebar دەردەکەوێت)
    st.markdown("""
        <style>
            [data-testid="stSidebar"] { display: block !important; }
        </style>
    """, unsafe_allow_html=True)

    user = get_user_data(st.session_state.username)
    if not user: st.stop()
    used, limit = user['used_tokens'], user['token_limit']
    balance_left = limit - used

    # --- SIDEBAR (Dark Blue & Icons) ---
    with st.sidebar:
        st.markdown(f"<h3 style='text-align:center; margin-top:0;'>Zirak AI <span style='font-size:12px; opacity:0.7;'>PRO</span></h3>", unsafe_allow_html=True)
        st.write("") # Space
        
        expert = st.radio("بەشەکان", [
            "🧠 مێشکی کۆرسەکە", 
            "🗣️ وەرگێڕی بازرگانی", 
            "📐 حاسیبەی لۆجستی", 
            "✍️ ستراتیژیستی ناوەڕۆک", 
            "📈 ڕاپۆرتی نهێنی"
        ], label_visibility="collapsed")
        
        st.divider()
        
        # بەشی باڵانس (Progress Bar)
        st.markdown(f"""
            <div style='background:rgba(255,255,255,0.05); padding:15px; border-radius:12px;'>
                <div style='display:flex; justify-content:space-between; font-size:14px; margin-bottom:5px;'>
                    <span>پاکێجی Pro</span>
                    <span style='color:#FF6600;'>{balance_left} ماوە</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.progress(min(used/limit, 1.0))
        
        st.write("")
        if st.button("چوونەدەرەوە"):
            st.session_state.logged_in = False
            st.rerun()

    # --- MAIN CONTENT ---
    
    # Initialize Messages
    if "messages" not in st.session_state: st.session_state.messages = []
    if "last_expert" not in st.session_state or st.session_state.last_expert != expert:
        st.session_state.messages = [] 
        st.session_state.last_expert = expert

    # Header