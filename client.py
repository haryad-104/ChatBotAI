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

# --- 2. MOBILE-FIRST RESPONSIVE UI (CSS) ---
st.set_page_config(page_title="Zirak AI", page_icon="🦁", layout="centered")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@300;400;700;900&display=swap');
        
        /* ستایلی گشتی */
        html, body, [class*="css"] {
            font-family: 'Noto Sans Arabic', sans-serif;
            direction: rtl;
            background-color: #f9fafb;
        }

        /* چاککردنی سایدبار بۆ مۆبایل */
        [data-testid="stSidebar"] {
            background-color: #0f172a !important;
            color: white !important;
        }
        [data-testid="stSidebar"] * { color: white !important; }

        /* --- زیرەککردنی دوگمەی پاشکۆ (Floating Action Button) --- */
        [data-testid="stPopover"] {
            position: fixed !important;
            z-index: 1000;
        }

        /* Desktop Mode */
        @media only screen and (min-width: 769px) {
            [data-testid="stPopover"] {
                bottom: 100px !important;
                right: calc(50% - 380px) !important;
            }
        }

        /* Mobile & Tablet Mode (ڕێکخستنی شوێنی دوگمەکە بۆ مۆبایل) */
        @media only screen and (max-width: 768px) {
            [data-testid="stPopover"] {
                bottom: 85px !important;
                right: 20px !important;
            }
            .expert-header { padding: 10px 15px !important; }
            .expert-header h3 { font-size: 16px !important; }
        }

        [data-testid="stPopover"] button {
            background: linear-gradient(135deg, #FF6600 0%, #E65C00 100%) !important;
            color: white !important;
            border-radius: 50% !important;
            width: 50px !important;
            height: 50px !important;
            border: 2px solid white !important;
            box-shadow: 0 4px 15px rgba(255, 102, 0, 0.4) !important;
        }

        /* کارتەکانی باڵانس (Responsive Stats) */
        .stat-container {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 20px;
        }
        .stat-card {
            flex: 1;
            min-width: 140px;
            background: white;
            padding: 15px;
            border-radius: 15px;
            border: 1px solid #e5e7eb;
            text-align: center;
        }

        /* سەردێڕی پسپۆڕەکان */
        .expert-header {
            background: white;
            padding: 20px;
            border-radius: 20px;
            border-right: 6px solid #FF6600;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS (Stay Efficient) ---
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
    # (Simplified Expert Brain)
    expert_instruction = f"You are an AI expert in {expert_name}. Answer precisely in Kurdish Sorani."
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    contents = []
    for msg in history[-6:]: contents.append({"role": "user" if msg['role'] == "user" else "model", "parts": [{"text": msg['content']}]})
    contents.append({"role": "user", "parts": [{"text": f"{expert_instruction}\nInput: {prompt}"}]})
    try:
        res = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps({"contents": contents}))
        data = res.json()
        return data['candidates'][0]['content']['parts'][0]['text'], data.get('usageMetadata', {}).get('totalTokenCount', 0)
    except: return "🔴 کێشەیەکی کاتی هەیە.", 0

# --- 4. MAIN APP LOGIC ---
def main():
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False

    if not st.session_state.logged_in:
        # چوونەژوورەوەی سادە و جوان
        st.markdown("<h1 style='text-align:center; color:#FF6600;'>🦁 بازرگانی زیرەک</h1>", unsafe_allow_html=True)
        u = st.text_input("Username").strip()
        p = st.text_input("Password", type="password").strip()
        if st.button("چوونەژوورەوە", use_container_width=True):
            user = get_user_data(u)
            if user and str(user['password']) == str(p):
                st.session_state.logged_in, st.session_state.username = True, u
                st.rerun()
            else: st.error("زانیارییەکان هەڵەن")
        return

    # زانیاری بەکارهێنەر
    user = get_user_data(st.session_state.username)
    balance = user['token_limit'] - user['used_tokens']

    # سایدباری زیرەک
    with st.sidebar:
        st.markdown(f"### 👋 {st.session_state.username}")
        expert = st.radio("بەشەکان:", ["🧠 مێشکی کۆرسەکە", "🗣️ وەرگێڕی بازرگانی", "📐 حاسیبەی لۆجستی", "✍️ ستراتیژیستی ناوەڕۆک", "📈 ڕاپۆرتی مانگانە", "📊 باڵانسی من"])
        st.divider()
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # لاپەڕەی باڵانس (Responsive Cards)
    if expert == "📊 باڵانسی من":
        st.title("📊 دۆخی هەژمار")
        st.markdown(f"""
            <div class="stat-container">
                <div class="stat-card">
                    <p style="color:gray; font-size:12px;">پاکێج</p>
                    <p style="font-weight:bold;">{user['plan']}</p>
                </div>
                <div class="stat-card">
                    <p style="color:gray; font-size:12px;">تۆکنی ماوە</p>
                    <p style="color:#FF6600; font-weight:bold; font-size:20px;">{balance:,}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.progress(min(user['used_tokens']/user['token_limit'], 1.0))
        return

    # ڕووکاری چات
    st.markdown(f"<div class='expert-header'><h3>{expert}</h3></div>", unsafe_allow_html=True)

    if "messages" not in st.session_state or st.session_state.get("last_expert") != expert:
        st.session_state.messages = []
        st.session_state.last_expert = expert

    for m in st.session_state.messages:
        with st.chat_message(m["role"], avatar="🦁" if m["role"]=="assistant" else "👤"):
            st.markdown(m["content"])

    # دوگمەی پاشکۆی فایل (Responsive Popover)
    with st.popover("📎"):
        st.file_uploader("بارکردنی فایل", type=['png','jpg','pdf'])
        st.camera_input("وێنەگرتن")

    # ناردنی نامە
    if balance > 0:
        if prompt := st.chat_input("پرسیارەکەت بنووسە..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="👤"): st.markdown(prompt)

            with st.chat_message("assistant", avatar="🦁"):
                res_box = st.empty()
                with st.spinner("..."):
                    ans, cost = get_ai_response(prompt, st.session_state.messages[:-1], expert)
                    # Typing Effect
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