import streamlit as st
import requests
import pandas as pd

# --- Config ---
try:
    SUPABASE_URL = st.secrets["general"]["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["general"]["SUPABASE_KEY"]
except:
    st.error("❌ کلیلەکان نیین!")
    st.stop()

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# --- Design ---
st.set_page_config(page_title="Admin Panel", page_icon="🔐", layout="wide")
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;700&display=swap');
        * { font-family: 'Vazirmatn', sans-serif !important; direction: rtl; }
        .stApp { background-color: #f8f9fa; }
        div[data-testid="stMetricValue"] { color: #FF6600; }
    </style>
""", unsafe_allow_html=True)

# --- Functions ---
def get_all_users():
    res = requests.get(f"{SUPABASE_URL}/rest/v1/users?select=*", headers=HEADERS)
    return res.json() if res.status_code == 200 else []

def add_tokens(username, amount):
    # هێنانی باڵانسی ئێستا
    res = requests.get(f"{SUPABASE_URL}/rest/v1/users?username=eq.{username}&select=used_tokens", headers=HEADERS)
    current_used = res.json()[0]['used_tokens']
    
    # کەمکردنەوەی بەکارهێنان واتە زیادکردنی باڵانس
    new_used = max(0, current_used - amount)
    
    requests.patch(f"{SUPABASE_URL}/rest/v1/users?username=eq.{username}", 
                   headers=HEADERS, json={"used_tokens": new_used})

# --- Main Admin UI ---
def main():
    st.title("🔐 ژووری کۆنتڕۆڵ")
    
    password = st.sidebar.text_input("پاسۆردی ئەدمین", type="password")
    if password != "admin123":
        st.warning("تکایە پاسۆرد بنووسە")
        return

    users = get_all_users()
    if users:
        df = pd.DataFrame(users)
        
        # 1. خشتەی بەکارهێنەران
        st.subheader("👥 بەکارهێنەران")
        st.dataframe(df[['username', 'plan', 'used_tokens', 'token_limit']], use_container_width=True)
        
        # 2. زیادکردنی باڵانس
        st.markdown("---")
        st.subheader("🔋 زیادکردنی باڵانس")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            target_user = st.selectbox("ناوی بەکارهێنەر", [u['username'] for u in users])
        with c2:
            amount = st.number_input("بڕی زیادکردن (Tokens)", value=50000, step=10000)
        with c3:
            st.write("")
            st.write("")
            if st.button("زیادکردن ➕", type="primary"):
                add_tokens(target_user, amount)
                st.success(f"پیرۆزە! {amount} بۆ {target_user} زیادکرا.")
                st.rerun()

if __name__ == "__main__":
    main()