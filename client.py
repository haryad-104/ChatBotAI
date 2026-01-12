import streamlit as st
import requests
import json
import time

# --- 1. CONFIG & SECURITY ---
st.set_page_config(page_title="Zirak AI", page_icon="🔹", layout="wide", initial_sidebar_state="collapsed")

# Initialize Session State
if 'theme' not in st.session_state: st.session_state.theme = 'light'
if 'sidebar_open' not in st.session_state: st.session_state.sidebar_open = True

# Load Secrets (Real Database Credentials)
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    GEMINI_API_KEY = st.secrets["GEMINI_KEY"]
except:
    st.error("⚠️ کێشە لە پەیوەندی: تکایە دڵنیابە فایلی secrets.toml ڕێکخراوە.")
    st.stop()

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# --- 2. THEME ENGINE & CSS ---
def get_theme_colors():
    if st.session_state.theme == 'light':
        return {
            "bg": "#ffffff", "text": "#1e293b", "sidebar_bg": "#f8fafc", "sidebar_text": "#334155",
            "input_bg": "#f1f5f9", "input_border": "#e2e8f0", "accent": "#2563eb", "card_bg": "#ffffff", "shadow": "rgba(0,0,0,0.05)"
        }
    else:
        return {
            "bg": "#0f172a", "text": "#f1f5f9", "sidebar_bg": "#1e293b", "sidebar_text": "#e2e8f0",
            "input_bg": "#334155", "input_border": "#475569", "accent": "#3b82f6", "card_bg": "#1e293b", "shadow": "rgba(0,0,0,0.3)"
        }

colors = get_theme_colors()
sidebar_pos = "0px" if st.session_state.sidebar_open else "320px"

st.markdown(f"""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@400;500;700;900&display=swap');
        * {{ font-family: 'Noto Sans Arabic', sans-serif !important; transition: background-color 0.3s, color 0.3s; }}
        .stApp {{ background-color: {colors['bg']}; color: {colors['text']}; }}
        
        /* HEADER */
        .custom-header {{
            position: fixed; top: 0; left: 0; width: 100%; height: 70px;
            background-color: {colors['bg']}; border-bottom: 1px solid {colors['input_border']};
            z-index: 1000; display: flex; align-items: center; justify-content: space-between;
            padding: 0 20px; direction: rtl;
        }}
        .header-title {{ font-weight: 900; font-size: 22px; color: {colors['accent']}; display: flex; align-items: center; gap: 10px; }}

        /* SIDEBAR */
        .custom-sidebar {{
            position: fixed; top: 70px; right: 0; width: 300px; height: calc(100vh - 70px);
            background-color: {colors['sidebar_bg']}; border-left: 1px solid {colors['input_border']};
            z-index: 999; transform: translateX({sidebar_pos});
            transition: transform 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
            padding: 20px; direction: rtl; overflow-y: auto;
            box-shadow: -5px 0 15px {colors['shadow']};
        }}

        /* CONTENT */
        .main-content {{
            margin-top: 80px;
            margin-right: { "300px" if st.session_state.sidebar_open else "0px" };
            transition: margin-right 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
            padding: 20px;
        }}
        @media (max-width: 768px) {{ .main-content {{ margin-right: 0px !important; }} }}

        /* WIDGETS */
        .stButton > button {{ background-color: {colors['accent']} !important; color: white !important; border-radius: 12px !important; padding: 10px 20px !important; border: none !important; }}
        .stTextInput input {{ background-color: {colors['input_bg']} !important; border: 1px solid {colors['input_border']} !important; color: {colors['text']} !important; border-radius: 12px !important; }}
        .stChatMessage {{ background-color: {colors['card_bg']} !important; border: 1px solid {colors['input_border']} !important; border-radius: 16px !important; }}
        
        [data-testid="stSidebar"], header[data-testid="stHeader"], #MainMenu, footer {{ display: none !important; }}
    </style>
""", unsafe_allow_html=True)

# --- 3. DATABASE FUNCTIONS (REAL) ---
def toggle_theme(): st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'
def toggle_sidebar(): st.session_state.sidebar_open = not st.session_state.sidebar_open

# هەموو کشێکان لابراون، ئێستا تەنها سەیری داتابەیس دەکات
def get_user_data(username):
    try:
        # Check 'users' table in Supabase
        url = f"{SUPABASE_URL}/rest/v1/users?username=eq.{username}&select=*"
        res = requests.get(url, headers=HEADERS)
        if res.status_code == 200:
            data = res.json()
            if len(data) > 0:
                return data[0] # بەکارهێنەر دۆزرایەوە
        return None
    except Exception as e:
        st.error(f"DB Error: {e}")
        return None

def update_tokens(username, current_used, cost):
    try:
        new_total = current_used + cost
        url = f"{SUPABASE_URL}/rest/v1/users?username=eq.{username}"
        requests.patch(url, headers=HEADERS, json={"used_tokens": new_total})
    except: pass

def save_chat_log(username, role, content, expert):
    try:
        url = f"{SUPABASE_URL}/rest/v1/chat_history"
        requests.post(url, headers=HEADERS, json={
            "username": username, "role": role, "content": content, "expert": expert
        })
    except: pass

def get_ai_response(prompt, history, expert):
    # لێرەدا دەبێت Promptی تایبەت بە پسپۆڕەکان بنووسیتەوە
    expert_instruction = f"You are an expert in {expert}. Answer in Kurdish."
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    contents = []
    for msg in history[-6:]: 
        contents.append({"role": "user" if msg['role'] == "user" else "model", "parts": [{"text": msg['content']}]})
    contents.append({"role": "user", "parts": [{"text": f"{expert_instruction}\nInput: {prompt}"}]})
    
    try:
        res = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps({"contents": contents}))
        data = res.json()
        text = data['candidates'][0]['content']['parts'][0]['text']
        tokens = data.get('usageMetadata', {}).get('totalTokenCount', 0)
        return text, tokens
    except: return "⚠️ هەڵەیەک لە سێرڤەر هەیە.", 0

# --- 4. APP STRUCTURE ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# HEADER (Visible Always)
st.markdown(f"""
    <div class="custom-header">
        <div class="header-title"><i class="fa-solid fa-layer-group"></i> Zirak AI</div>
        <div></div>
    </div>
""", unsafe_allow_html=True)

# Controls (Invisible Overlay)
col_h1, col_h2, col_h3 = st.columns([1, 8, 1])
if st.session_state.logged_in:
    with col_h1:
        if st.button("☰", key="menu_toggle"): toggle_sidebar(); st.rerun()
with col_h3:
    if st.button("🌓", key="theme_toggle"): toggle_theme(); st.rerun()

# --- 5. LOGIN OR MAIN ---
if not st.session_state.logged_in:
    # --- LOGIN PAGE ---
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown(f"""
        <div style="background:{colors['card_bg']}; padding:40px; border-radius:24px; box-shadow:0 10px 30px {colors['shadow']}; text-align:center; border:1px solid {colors['input_border']};">
            <div style="width:60px; height:60px; background:{colors['accent']}; border-radius:16px; margin:0 auto 20px auto; display:flex; align-items:center; justify-content:center; color:white; font-size:28px;">
                <i class="fa-solid fa-robot"></i>
            </div>
            <h2 style="color:{colors['text']}; margin:0;">بەخێربێیتەوە</h2>
            <p style="color:{colors['sidebar_text']}; font-size:14px; margin-bottom:30px;">تکایە زانیارییەکانت بنووسە</p>
        </div>
        """, unsafe_allow_html=True)
        
        u = st.text_input("نازناو", placeholder="Username").strip()
        p = st.text_input("وشەی نهێنی", type="password", placeholder="••••••••").strip()
        
        if st.button("چوونەژوورەوە", use_container_width=True):
            with st.spinner("پەیوەندی بە داتابەیس..."):
                user = get_user_data(u)
                if user and str(user['password']) == str(p):
                    st.session_state.logged_in = True
                    st.session_state.username = u
                    st.session_state.user_info = user
                    st.rerun()
                else:
                    st.error("زانیارییەکان هەڵەن یان بەکارهێنەر نادۆزرایەوە.")

else:
    # --- MAIN PAGE ---
    
    # 1. Sidebar Logic
    with st.container():
        st.markdown('<div class="sidebar-logic-container">', unsafe_allow_html=True)
        st.markdown(f"""
        <style>
            div[data-testid="stVerticalBlock"] > div:has(div.sidebar-buttons) {{
                position: fixed; top: 180px; right: { "20px" if st.session_state.sidebar_open else "-300px" };
                width: 260px; z-index: 1001; transition: right 0.4s; direction: rtl;
            }}
        </style>
        <div class="sidebar-buttons"></div>
        """, unsafe_allow_html=True)
        
        # Profile Card
        st.markdown(f"""
        <div style="margin-bottom: 20px; padding: 10px; background: {colors['input_bg']}; border-radius: 12px; display: flex; align-items: center; gap: 10px;">
            <div style="width: 40px; height: 40px; background: {colors['accent']}; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold;">
                {st.session_state.username[0].upper()}
            </div>
            <div>
                <div style="font-weight: bold; font-size: 14px; color:{colors['text']}">{st.session_state.username}</div>
                <div style="font-size: 11px; opacity: 0.7; color:{colors['sidebar_text']}">{st.session_state.user_info.get('plan', 'Basic')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if 'expert' not in st.session_state: st.session_state.expert = "🧠 مێشکی کۆرسەکە"
        
        menu = [
            {"icon": "fa-brain", "label": "مێشکی کۆرسەکە"},
            {"icon": "fa-language", "label": "وەرگێڕی بازرگانی"},
            {"icon": "fa-calculator", "label": "حاسیبەی لۆجستی"},
            {"icon": "fa-pen-nib", "label": "ستراتیژیستی ناوەڕۆک"},
            {"icon": "fa-wallet", "label": "باڵانسی من"},
        ]

        for item in menu:
            label = item['label']
            is_active = st.session_state.expert == label
            bt_c1, bt_c2 = st.columns([1, 5])
            with bt_c1: st.markdown(f'<div style="text-align:center; padding-top:8px; color:{colors["accent"] if is_active else colors["sidebar_text"]};"><i class="fa-solid {item["icon"]}"></i></div>', unsafe_allow_html=True)
            with bt_c2:
                if st.button(label, key=f"nav_{label}", use_container_width=True):
                    st.session_state.expert = label
                    st.rerun()
        
        st.markdown("<hr style='opacity:0.1'>", unsafe_allow_html=True)
        if st.button("چوونە دەرەوە", key="logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # 2. Main Content
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
    expert = st.session_state.expert
    st.markdown(f"""
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:20px;">
            <h2 style="margin:0; color:{colors['text']};">{expert}</h2>
            <span style="background:{colors['accent']}20; color:{colors['accent']}; padding:2px 10px; border-radius:20px; font-size:12px; font-weight:bold;">Active</span>
        </div>
    """, unsafe_allow_html=True)

    if expert == "fa-wallet" or "باڵانس" in expert:
        # Balance Page
        user_info = get_user_data(st.session_state.username) # Refresh data
        used = user_info.get('used_tokens', 0)
        limit = user_info.get('token_limit', 100)
        c1, c2 = st.columns(2)
        c1.metric("تۆکنی ماوە", f"{limit - used:,}")
        c2.metric("پاکێج", user_info.get('plan', 'Free'))
        st.progress(min(used/limit, 1.0))
    else:
        # Chat Page
        if "messages" not in st.session_state: st.session_state.messages = []
        
        for m in st.session_state.messages:
            with st.chat_message(m["role"], avatar="🦁" if m["role"]=="assistant" else "👤"):
                st.markdown(m["content"])

        if prompt := st.chat_input("لێرە بنووسە..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="👤"): st.markdown(prompt)
            
            with st.chat_message("assistant", avatar="🦁"):
                res_box = st.empty()
                with st.spinner("..."):
                    response_text, cost = get_ai_response(prompt, st.session_state.messages[:-1], expert)
                    # Typing Effect
                    full_res = ""
                    for word in response_text.split():
                        full_res += word + " "
                        res_box.markdown(full_res + "▌")
                        time.sleep(0.02)
                    res_box.markdown(full_res)
            
            # Save & Update
            st.session_state.messages.append({"role": "assistant", "content": full_res})
            save_chat_log(st.session_state.username, "user", prompt, expert)
            save_chat_log(st.session_state.username, "assistant", full_res, expert)
            
            # Update Tokens in Real-time
            current_used = st.session_state.user_info.get('used_tokens', 0)
            update_tokens(st.session_state.username, current_used, cost)
            st.session_state.user_info['used_tokens'] += cost # Local update for UI speed

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="custom-sidebar"></div>', unsafe_allow_html=True)