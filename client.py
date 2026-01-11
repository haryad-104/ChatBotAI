import streamlit as st
import requests
import json
import os
import time

# --- 1. CONFIG & SECRETS (شێوازی ڕاستەوخۆ) ---
# تێبینی: کلیلەکانت لێرە دابنێ لەنێوان دوو کەوانەکە "..."
SUPABASE_URL = "https://oowfvezpskatjyidwgni.supabase.co"
SUPABASE_KEY = "sb_publishable_Wj0b2PvfmQn5T5QMlp_yHA_fVs4y4mt"
GEMINI_API_KEY = "AIzaSyC4WC1eBy3S_QdUVrT7qz0PAn3QAhme8vE"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# --- 2. UI & CSS HACKS ---
st.set_page_config(page_title="Zirak AI", page_icon="🦁", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Vazirmatn', sans-serif;
            direction: rtl;
        }
        
        header {visibility: hidden;}
        footer {visibility: hidden;}
        
        [data-testid="stPopover"] {
            position: fixed;
            bottom: 80px;
            right: 20px;
            z-index: 9999;
            background-color: white;
            border-radius: 50%;
            box-shadow: 0 4px 10px rgba(0,0,0,0.2);
            width: 50px;
            height: 50px;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 2px solid #FF6600;
        }
        
        [data-testid="stPopover"] button {
            border: none;
            background: transparent;
            color: #FF6600;
            font-size: 20px;
        }

        .expert-tag {
            background-color: #fff7ed;
            color: #c2410c;
            padding: 8px 20px;
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