import streamlit as st
import requests
import json
import os
import time

# --- 1. CONFIG & SECRETS (Fixed Security) ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    GEMINI_API_KEY = st.secrets["GEMINI_KEY"]
except:
    st.error("⚠️ Secrets configurated incorrectly.")
    st.stop()

HEADERS = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}

# --- 2. PREMIUM UI & UX DESIGN (THE FIX) ---
st.set_page_config(page_title="Zirak AI", page_icon="🦁", layout="centered", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@300;400;700;900&display=swap');
        
        /* 1. Global Styles */
        html, body, [class*="css"] {
            font-family: 'Noto Sans Arabic', sans-serif;
            direction: rtl;
            background-color: #fcfcfc;
        }

        /* 2. Sidebar Pro Look */
        [data-testid="stSidebar"] {
            background-color: #0f172a !important; /* Dark Navy */
            color: white !important;
            border-left: none;
        }
        [data-testid="stSidebar"] * { color: white !important; }
        [data-testid="stSidebarNav"] { background-color: transparent !important; }
        
        /* 3. Floating Attachment Button (Smart Position) */
        [data-testid="stPopover"] {
            position: fixed !important;
            bottom: 90px !important; /* ڕێک لە سەروو چات بارەکە */
            right: 50% !important;
            transform: translateX(320px) !important; /* دەیکاتە لای ڕاستی چاتەکە */
            z-index: 999;
        }
        
        @media only screen and (max-width: 768px) {
            [data-testid="stPopover"] {
                transform: translateX(160px) !important;
                bottom: 85px !important;
            }
        }

        [data-testid="stPopover"] button {
            background: #FF6600 !important;
            color: white !important;
            border-radius: 50% !important;
            width: 45px !important;
            height: 45px !important;
            border: 3px solid white !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
        }

        /* 4. Expert Badge Styling */
        .expert-header {
            background: linear-gradient(90deg, #f8fafc 0%, #eff6ff 100%);
            padding: 15px 25px;
            border-radius: 15px;
            border-right: 5px solid #FF6600;
            margin-bottom: 25px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.02);
        }

        /* 5. Chat Bubbles Fix */
        .stChatMessage { 
            background-color: white !important; 
            border: 1px solid #f1f5f9 !important;
            border-radius: 15px !important;
            padding: 15px !important;
            margin-bottom: 10px !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.01) !important;
        }

        /* 6. Customizing Inputs */
        .stTextInput input, .stSelectbox div {
            border-radius: 12px !important;
        }
        
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. DATABASE FUNCTIONS (STAY THE SAME) ---
@st.cache_data(ttl=300)
def get_user_data(username):
    try:
        url = f"{SUPABASE_URL}/rest/v1/users?username=eq.{username}&select=*"
        res = requests.get(url, headers=HEADERS)
        return res.json()[0] if res.status_code == 200 and res.json() else None
    except: return None

def update_tokens_db(username, new_total):
    requests.patch(f"{SUPABASE_URL}/rest/v1/users?username=eq.{username}", headers=HEADERS, json={"used_tokens": new_total})
    get_user_data.clear()

def save_chat(username, role, content, expert):
    requests.post(f"{SUPABASE_URL}/rest/v1/chat_history", headers=HEADERS, json={"username": username, "role": role, "content": content, "expert": expert})

# --- 4. EXPERT BRAIN LOGIC ---
def get_expert_prompt(expert_name):
    # (ئێرە وەک خۆیەتی بەڵام بە کورتی دەینووسم)
    prompts = {
        "🧠 مێشکی کۆرسەکە": "Role: Course Expert. Answer only from content.",
        "🗣️ وەرگێڕی بازرگانی": "Role: Professional Translator. Kurdish <-> English.",
        "📐 حاسیبەی لۆجستی": "Role: Calculator. Output numbers only.",
        "✍️ ستراتیژیستی ناوەڕۆک": "Role: Creative Marketer.",
        "📈 ڕاپۆرتی نهێنی": "Role: Data Analyst.",
    }
    for key in prompts:
        if key in expert_name: return prompts[key]
    return "Helpful Assistant."

def get_ai_response(prompt, history, expert_prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    contents = []
    for msg in history[-6:]: contents.append({"role": "user" if msg['role'] == "user" else "model", "parts": [{"text": msg['content']}]})
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

    if not st.session_state.logged_in:
        # --- LOGIN SCREEN ---
        st.markdown("<br><h1 style='text-align:center; color:#FF6600;'>🦁 بازرگانی زیرەک</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("چوونەژوورەوە", use_container_width=True):
                user = get_user_data(u.strip())
                if user and str(user['password']) == str(p.strip()):
                    st.session_state.logged_in, st.session_state.username = True, u.strip()
                    st.rerun()
                else: st.error("❌ زانیاری هەڵەیە!")
        return

    # --- LOGGED IN UI ---
    user = get_user_data(st.session_state.username)
    if not user: st.stop()
    balance_left = user['token_limit'] - user['used_tokens']

    with st.sidebar:
        st.markdown(f"### 👋 {st.session_state.username}")
        expert = st.radio("بەشە پسپۆڕەکان:", [
            "🧠 مێشکی کۆرسەکە", "🗣️ وەرگێڕی بازرگانی", "📐 حاسیبەی لۆجستی", 
            "✍️ ستراتیژیستی ناوەڕۆک", "📈 ڕاپۆرتی نهێنی", "📊 باڵانسی من"
        ])
        st.divider()
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # Route: Balance
    if expert == "📊 باڵانسی من":
        st.title("📊 باڵانس و بەکارهێنان")
        st.metric("تۆکنی ماوە", f"{balance_left:,}")
        st.progress(min(user['used_tokens']/user['token_limit'], 1.0))
        return

    # Expert Header
    st.markdown(f"<div class='expert-header'><h3>{expert}</h3></div>", unsafe_allow_html=True)

    # Chat Management
    if "messages" not in st.session_state or st.session_state.get("last_expert") != expert:
        st.session_state.messages = []
        st.session_state.last_expert = expert

    for m in st.session_state.messages:
        with st.chat_message(m["role"], avatar="🦁" if m["role"]=="assistant" else "👤"):
            st.markdown(m["content"])

    # --- ATTACHMENTS (SMART POPOVER) ---
    with st.popover("📎"):
        st.caption("بارکردنی وێنە یان PDF")
        uploaded_file = st.file_uploader("", type=['png','jpg','pdf'], label_visibility="collapsed")
        camera_img = st.camera_input("وێنەی ڕاستەوخۆ", label_visibility="collapsed")

    # Chat Input
    if balance_left > 0:
        if prompt := st.chat_input("پرسیارەکەت لێرە بنووسە..."):
            if uploaded_file or camera_img: prompt += " [Attached File]"
            
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="👤"): st.markdown(prompt)

            with st.chat_message("assistant", avatar="🦁"):
                placeholder = st.empty()
                with st.spinner("..."):
                    resp, cost = get_ai_response(prompt, st.session_state.messages[:-1], get_expert_prompt(expert))
                    # Typing Effect
                    full_resp = ""
                    for word in resp.split():
                        full_resp += word + " "
                        placeholder.markdown(full_resp + "▌")
                        time.sleep(0.02)
                    placeholder.markdown(full_resp)

            st.session_state.messages.append({"role": "assistant", "content": full_resp})
            save_chat(st.session_state.username, "user", prompt, expert)
            save_chat(st.session_state.username, "assistant", full_resp, expert)
            update_tokens_db(st.session_state.username, user['used_tokens'] + cost)
    else:
        st.error("⚠️ باڵانسی تۆکنەکانت تەواو بووە.")

if __name__ == "__main__":
    main()