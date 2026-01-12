import streamlit as st
import requests
import json
import os
import time

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

# --- 2. UI & CSS HACKS (SIDEBAR FIXED) ---
# گۆڕانکاری گرنگ: لێرە کردمان بە "expanded"
# ئەمە وا دەکات لە لاپتۆپ کراوە بێت، بەڵام لە مۆبایل دەبێتە مێنۆ
st.set_page_config(page_title="Zirak AI", page_icon="🦁", layout="centered", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Vazirmatn', sans-serif;
            direction: rtl;
        }
        
        /* شاردنەوەی باکگراوندی هێدەر بەبێ شاردنەوەی دوگمەکان */
        header[data-testid="stHeader"] {
            background-color: transparent;
            z-index: 1;
        }
        /* دڵنیابوون لەوەی دوگمەی مێنۆ (سێ هێڵەکە) دیار بێت */
        [data-testid="stSidebarCollapsedControl"] {
            display: block !important;
            color: #FF6600 !important;
        }
        
        footer {visibility: hidden;}
        
        /* --- دوگمەی فایل (Smart Floating Button) --- */
        [data-testid="stPopover"] {
            position: fixed !important;
            z-index: 999999 !important;
            background-color: white !important;
            border-radius: 50% !important;
            border: 2px solid #FF6600 !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            transition: all 0.3s ease !important;
        }
        
        [data-testid="stPopover"] > div {
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            width: 100% !important;
            height: 100% !important;
        }

        /* ستایلی لاپتۆپ */
        @media only screen and (min-width: 600px) {
            [data-testid="stPopover"] {
                bottom: 110px !important;
                right: 30px !important; /* کەمێک دوورتر لە لێوارەکە */
                width: 60px !important;
                height: 60px !important;
            }
            [data-testid="stPopover"]:hover {
                transform: scale(1.1) !important;
                box-shadow: 0 6px 18px rgba(255, 102, 0, 0.4) !important;
            }
        }

        /* ستایلی مۆبایل */
        @media only screen and (max-width: 600px) {
            [data-testid="stPopover"] {
                bottom: 140px !important;
                right: 20px !important;
                width: 50px !important;
                height: 50px !important;
            }
        }
        
        [data-testid="stPopover"] button {
            border: none !important;
            background: transparent !important;
            color: #FF6600 !important;
            font-size: 24px !important;
            padding: 0 !important;
            margin: 0 !important;
            line-height: 1 !important;
        }

        .expert-tag {
            background-color: #fff7ed;
            color: #c2410c;
            padding: 8px 18px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: bold;
            display: inline-block;
            margin-bottom: 20px;
            border: 1px solid #ffedd5;
        }
        
        .stChatMessage { direction: rtl; text-align: right; }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNCTIONS ---
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
    payload = {"username": username, "role": role, "content": content, "expert": expert}
    requests.post(f"{SUPABASE_URL}/rest/v1/chat_history", headers=HEADERS, json=payload)

def get_expert_prompt(expert_name):
    course_context = ""
    if os.path.exists("course_info.txt"):
        with open("course_info.txt", "r", encoding="utf-8") as f: course_context = f.read()
    
    report_context = ""
    if os.path.exists("monthly_report.txt"):
        with open("monthly_report.txt", "r", encoding="utf-8") as f: report_context = f.read()

    prompts = {
        "🧠 مێشکی کۆرسەکە": f"Role: Course Expert. Source: {course_context}. Rule: Only answer from source. If outside topic, refuse politely.",
        "🗣️ وەرگێڕی بازرگانی": "Role: Translator. Task: Translate Kurdish <-> Business English. Style: Formal, Precise. No chatting.",
        "📐 حاسیبەی لۆجستی": "Role: Calculator. Task: Calculate CBM ((L*W*H)/1000000) or Volumetric Weight ((L*W*H)/5000). Output ONLY the number.",
        "✍️ ستراتیژیستی ناوەڕۆک": "Role: Marketing Creative. Task: Create captions, ideas, hashtags. Style: Exciting.",
        "📈 ڕاپۆرتی نهێنی": f"Role: Insider Analyst. Source: {report_context}. Rule: Only use this report. Refuse old data.",
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

# --- 4. MAIN APP ---
def main():
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.markdown("<br><h2 style='text-align:center;'>🦁 بازرگانی زیرەک</h2>", unsafe_allow_html=True)
        with st.container():
            u = st.text_input("ناوی بەکارهێنەر")
            p = st.text_input("وشەی نهێنی", type="password")
            if st.button("چوونەژوورەوە", use_container_width=True):
                user = get_user_data(u.strip())
                if user and str(user['password']) == str(p.strip()):
                    st.session_state.logged_in = True
                    st.session_state.username = u.strip()
                    st.rerun()
                else: st.error("زانیاری هەڵەیە")
        return

    user = get_user_data(st.session_state.username)
    if not user: st.stop()
    used, limit = user['used_tokens'], user['token_limit']
    balance_left = limit - used

    with st.sidebar:
        st.markdown(f"**{st.session_state.username}**")
        expert = st.radio("بەشەکان:", [
            "🧠 مێشکی کۆرسەکە", "🗣️ وەرگێڕی بازرگانی", "📐 حاسیبەی لۆجستی", 
            "✍️ ستراتیژیستی ناوەڕۆک", "📈 ڕاپۆرتی نهێنی", "📊 باڵانسی من"
        ])
        st.divider()
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

    if expert == "📊 باڵانسی من":
        st.markdown("### 📊 دۆخی هەژمارەکەت")
        st.metric("تۆکنی ماوە", f"{balance_left:,}")
        st.progress(min(used/limit, 1.0))
        return

    st.markdown(f"<div class='expert-tag'>{expert}</div>", unsafe_allow_html=True)

    if "messages" not in st.session_state: st.session_state.messages = []
    if "last_expert" not in st.session_state or st.session_state.last_expert != expert:
        st.session_state.messages = [] 
        st.session_state.last_expert = expert

    for m in st.session_state.messages:
        with st.chat_message(m["role"], avatar="🦁" if m["role"]=="assistant" else "👤"):
            st.markdown(m["content"])

    with st.popover("📎", use_container_width=False):
        st.caption("زیادکردنی فایل")
        uploaded_file = st.file_uploader("", type=['png','jpg','pdf'], label_visibility="collapsed")
        camera_img = st.camera_input("وێنەگرتن", label_visibility="collapsed")

    if uploaded_file or camera_img:
        st.info("✅ فایل ئامادەیە. پرسیارەکەت بنووسە.")

    if balance_left > 0:
        if prompt := st.chat_input("لێرە بنووسە..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="👤"): st.markdown(prompt)

            with st.chat_message("assistant", avatar="🦁"):
                placeholder = st.empty()
                with st.spinner("..."):
                    specific_brain = get_expert_prompt(expert)
                    if uploaded_file or camera_img: prompt += " [Attached File]"
                    
                    full_text, cost = get_ai_response(prompt, st.session_state.messages[:-1], specific_brain)
                    
                    displayed_text = ""
                    for word in full_text.split():
                        displayed_text += word + " "
                        placeholder.markdown(displayed_text + "▌")
                        time.sleep(0.03)
                    placeholder.markdown(displayed_text)

            st.session_state.messages.append({"role": "assistant", "content": full_text})
            save_chat(st.session_state.username, "user", prompt, expert)
            save_chat(st.session_state.username, "assistant", full_text, expert)
            update_tokens_db(st.session_state.username, used + cost)
    else:
        st.error("⚠️ باڵانس تەواو بووە.")

if __name__ == "__main__":
    main()