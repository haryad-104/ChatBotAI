import streamlit as st
import requests
import json
import time

# --- 1. CONFIG & SECRETS ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    GEMINI_API_KEY = st.secrets["GEMINI_KEY"]
except:
    st.error("⚠️ کلیلەکان بە دروستی ڕێنەخراون.")
    st.stop()

HEADERS = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}

# --- 2. PIXEL-PERFECT UI SETUP ---
st.set_page_config(page_title="Zirak AI", page_icon="🦁", layout="wide", initial_sidebar_state="expanded")

def load_css(login_mode=False):
    # دیاریکردنی ستایل بەپێی ئەوەی لە Loginین یان Chat
    bg_color = "#f3f4f6" if login_mode else "#ffffff"
    
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@400;500;700;900&display=swap');
        
        * {{ font-family: 'Noto Sans Arabic', sans-serif !important; }}
        
        /* Global Settings */
        .stApp {{
            background-color: {bg_color};
            direction: rtl;
        }}
        
        /* --- LOGIN CARD STYLES --- */
        .login-container {{
            background: white;
            padding: 40px;
            border-radius: 24px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.08);
            text-align: center;
            max-width: 400px;
            margin: auto;
            border: 1px solid #f0f0f0;
        }}
        
        .login-logo {{
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #FF6600, #ff8533);
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 20px auto;
            color: white;
            font-size: 30px;
            box-shadow: 0 4px 15px rgba(255, 102, 0, 0.3);
        }}
        
        /* Customizing Streamlit Inputs for Login */
        div[data-testid="stTextInput"] input {{
            background-color: #f9fafb !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 12px !important;
            padding: 10px 15px !important;
            font-size: 16px !important;
            color: #1f2937 !important;
            direction: rtl;
        }}
        div[data-testid="stTextInput"] input:focus {{
            border-color: #FF6600 !important;
            box-shadow: 0 0 0 2px rgba(255,102,0,0.1) !important;
        }}
        
        /* Login Button (Dark Navy as per screenshot) */
        .login-btn button {{
            background-color: #0f172a !important;
            color: white !important;
            width: 100%;
            border-radius: 12px !important;
            padding: 12px 0 !important;
            font-weight: bold !important;
            font-size: 16px !important;
            border: none !important;
            transition: all 0.2s;
        }}
        .login-btn button:hover {{
            background-color: #1e293b !important;
            transform: translateY(-2px);
        }}

        /* --- CHAT INTERFACE STYLES --- */
        [data-testid="stSidebar"] {{
            background-color: #0f172a !important; /* Dark Sidebar */
            border-right: none;
        }}
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span {{
            color: white !important;
        }}
        
        /* Chat Input Area */
        .stChatInputContainer {{
            padding-bottom: 20px;
        }}
        .stChatInput textarea {{
            background-color: #f3f4f6 !important;
            border-radius: 16px !important;
            border: none !important;
        }}
        
        /* Attach Button (Popover) */
        [data-testid="stPopover"] {{
            position: fixed !important;
            bottom: 85px !important;
            right: 20px !important;
            z-index: 9999;
        }}
        [data-testid="stPopover"] button {{
            background-color: #f3f4f6 !important;
            color: #6b7280 !important;
            border: none !important;
            border-radius: 12px !important;
            width: 45px !important;
            height: 45px !important;
        }}

        /* Hide Default Elements */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
        
    </style>
    """, unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---
@st.cache_data(ttl=300)
def get_user_data(username):
    try:
        url = f"{SUPABASE_URL}/rest/v1/users?username=eq.{username}&select=*"
        res = requests.get(url, headers=HEADERS)
        return res.json()[0] if res.status_code == 200 and res.json() else None
    except: return None

def update_tokens(username, new_total):
    requests.patch(f"{SUPABASE_URL}/rest/v1/users?username=eq.{username}", headers=HEADERS, json={"used_tokens": new_total})
    get_user_data.clear()

def save_chat(username, role, content, expert):
    requests.post(f"{SUPABASE_URL}/rest/v1/chat_history", headers=HEADERS, json={"username": username, "role": role, "content": content, "expert": expert})

def get_ai_response(prompt, history, expert_name):
    instruction = f"You are {expert_name}. Answer in Kurdish Sorani. Be helpful and precise."
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    contents = []
    for msg in history[-6:]: contents.append({"role": "user" if msg['role'] == "user" else "model", "parts": [{"text": msg['content']}]})
    contents.append({"role": "user", "parts": [{"text": f"{instruction}\nInput: {prompt}"}]})
    try:
        res = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps({"contents": contents}))
        data = res.json()
        return data['candidates'][0]['content']['parts'][0]['text'], data.get('usageMetadata', {}).get('totalTokenCount', 0)
    except: return "🔴 کێشە هەیە.", 0

# --- 4. MAIN APP ---
def main():
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False

    # ---------------- LOGIN SCREEN (MATCHING IMAGE 1) ----------------
    if not st.session_state.logged_in:
        load_css(login_mode=True)
        
        # Center the card
        col1, col2, col3 = st.columns([1, 1, 1]) # Make middle column wider on mobile if needed via CSS, here using balanced layout
        
        with col2:
            st.markdown("""
                <br><br>
                <div class="login-container">
                    <div class="login-logo">🦁</div>
                    <h2 style="margin:0; font-weight:900; color:#1f2937;">بەخێربێیتەوە</h2>
                    <p style="color:#6b7280; font-size:14px; margin-bottom:25px;">تکایە زانیارییەکانت بنووسە</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Inputs need to be OUTSIDE the HTML div to work as Streamlit widgets, 
            # but CSS styles them to look integrated.
            with st.container(): 
                # Using a container to apply specific margins if needed
                u = st.text_input("نازناو", placeholder="Username", label_visibility="visible")
                p = st.text_input("وشەی نهێنی", type="password", placeholder="••••••••", label_visibility="visible")
                
                st.markdown('<div class="login-btn">', unsafe_allow_html=True)
                if st.button("چوونەژوورەوە"):
                    user = get_user_data(u.strip())
                    if user and str(user['password']) == str(p.strip()):
                        st.session_state.logged_in, st.session_state.username = True, u.strip()
                        st.rerun()
                    else:
                        st.error("زانیاری هەڵەیە!")
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Close the visual container effect (Visual trickery via CSS margins on the column)
        return

    # ---------------- CHAT INTERFACE (MATCHING IMAGE 2) ----------------
    load_css(login_mode=False)
    user = get_user_data(st.session_state.username)
    if not user: st.stop()
    balance = user['token_limit'] - user['used_tokens']

    # --- Sidebar ---
    with st.sidebar:
        st.markdown(f"""
            <div style="text-align:center; margin-bottom:20px;">
                <div style="width:60px; height:60px; background:#FF6600; border-radius:15px; margin:auto; display:flex; align-items:center; justify-content:center; font-size:30px; color:white;">🤖</div>
                <h3 style="margin-top:10px; color:white;">Zirak AI</h3>
                <p style="color:#94a3b8; font-size:12px;">ALIBABA ASSISTANT</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### بەشەکان")
        expert = st.radio("", ["🧠 مێشکی کۆرسەکە", "🗣️ وەرگێڕی بازرگانی", "📐 حاسیبەی لۆجستی", "✍️ ستراتیژیستی ناوەڕۆک", "📈 ڕاپۆرتی نهێنی", "📊 باڵانسی من"], label_visibility="collapsed")
        
        st.divider()
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # --- Balance View ---
    if expert == "📊 باڵانسی من":
        st.title("📊 دۆخی هەژمار")
        st.info(f"پاکێج: {user['plan']}")
        st.metric("تۆکنی ماوە", f"{balance:,}")
        st.progress(min(user['used_tokens']/user['token_limit'], 1.0))
        return

    # --- Chat View ---
    # Header
    col_h1, col_h2 = st.columns([1, 5])
    with col_h1: st.markdown("### 🦁") # Icon placeholder
    with col_h2: st.markdown(f"### {expert}") # Title

    # Messages
    if "messages" not in st.session_state or st.session_state.get("last_expert") != expert:
        st.session_state.messages = []
        st.session_state.last_expert = expert

    # Render Empty State if no messages
    if not st.session_state.messages:
        st.markdown(f"""
            <div style="text-align:center; padding:50px; color:#9ca3af;">
                <div style="font-size:50px; margin-bottom:10px; opacity:0.3;">🧠</div>
                <h3>چۆن دەتوانم یارمەتیت بدەم؟</h3>
                <p>پرسیارێک بکە دەربارەی {expert}</p>
            </div>
        """, unsafe_allow_html=True)

    for m in st.session_state.messages:
        with st.chat_message(m["role"], avatar="🦁" if m["role"]=="assistant" else "👤"):
            st.markdown(m["content"])

    # Attachment Popover (Clean style like chat input)
    with st.popover("📎"):
        st.file_uploader("وێنە/فایل", type=['png','jpg','pdf'])
        st.camera_input("کامێرا")

    # Input Logic
    if balance > 0:
        if prompt := st.chat_input("پرسیارەکەت لێرە بنووسە..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="👤"): st.markdown(prompt)

            with st.chat_message("assistant", avatar="🦁"):
                res_box = st.empty()
                with st.spinner(""):
                    ans, cost = get_ai_response(prompt, st.session_state.messages[:-1], expert)
                    full_res = ""
                    for word in ans.split():
                        full_res += word + " "
                        res_box.markdown(full_res + "▌")
                        time.sleep(0.02)
                    res_box.markdown(full_res)

            st.session_state.messages.append({"role": "assistant", "content": full_res})
            save_chat(st.session_state.username, "user", prompt, expert)
            save_chat(st.session_state.username, "assistant", full_res, expert)
            update_tokens(st.session_state.username, user['used_tokens'] + cost)
    else:
        st.error("⚠️ باڵانست تەواو بووە.")

if __name__ == "__main__":
    main()