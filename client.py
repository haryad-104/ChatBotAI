import streamlit as st
import requests
import json
import time

# --- 1. CONFIG ---
st.set_page_config(page_title="Zirak AI", page_icon="🦁", layout="wide", initial_sidebar_state="collapsed")

# Session State Init
if 'theme' not in st.session_state: st.session_state.theme = 'light'
if 'sidebar_open' not in st.session_state: st.session_state.sidebar_open = True # Default Open on Desktop

# Secrets
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    GEMINI_API_KEY = st.secrets["GEMINI_KEY"]
except:
    st.error("⚠️ کێشە لە پەیوەندی داتابەیس.")
    st.stop()

HEADERS = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}

# --- 2. THEME COLORS ---
def get_colors():
    if st.session_state.theme == 'light':
        return {
            "bg": "#f8fafc", "text": "#1e293b", "nav": "#ffffff", 
            "accent": "#FF6600", "border": "#e2e8f0", "msg_bg": "#ffffff"
        }
    else:
        return {
            "bg": "#0f172a", "text": "#f1f5f9", "nav": "#1e293b", 
            "accent": "#FF6600", "border": "#334155", "msg_bg": "#1e293b"
        }

c = get_colors()

# --- 3. CSS (THE FIX) ---
# لێرەدا سایدبارەکە دەبەینە لای ڕاست و بۆشایی بۆ دادەنێین
sidebar_width = "300px"
main_margin = "300px" if st.session_state.sidebar_open else "0px"
sidebar_right = "0px" if st.session_state.sidebar_open else "-320px"

st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@400;500;700;900&display=swap');
        * {{ font-family: 'Noto Sans Arabic', sans-serif !important; }}
        
        .stApp {{
            background-color: {c['bg']};
            color: {c['text']};
        }}

        /* --- 1. RIGHT SIDEBAR FIX --- */
        .custom-sidebar {{
            position: fixed;
            top: 0;
            right: {sidebar_right};
            width: {sidebar_width};
            height: 100vh;
            background-color: {c['nav']};
            border-left: 1px solid {c['border']};
            z-index: 1000;
            transition: right 0.3s ease-in-out;
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            direction: rtl;
            box-shadow: -5px 0 15px rgba(0,0,0,0.05);
        }}

        /* --- 2. MAIN CONTENT SHIFT --- */
        .main-content-wrapper {{
            margin-right: {main_margin};
            transition: margin-right 0.3s ease-in-out;
            padding: 20px;
            direction: rtl;
        }}
        
        /* Mobile Fix: Overlay instead of push */
        @media (max-width: 768px) {{
            .main-content-wrapper {{ margin-right: 0px !important; }}
            .custom-sidebar {{ width: 85%; }}
        }}

        /* --- 3. HEADER & CONTROLS --- */
        .top-bar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 0;
            margin-bottom: 20px;
            border-bottom: 1px solid {c['border']};
        }}

        /* --- 4. UPLOAD SECTION --- */
        .upload-zone {{
            border: 2px dashed {c['border']};
            background-color: {c['bg']};
            border-radius: 12px;
            padding: 10px;
            margin-top: 10px;
            text-align: center;
        }}

        /* HIDE DEFAULT STREAMLIT ELEMENTS */
        [data-testid="stSidebar"] {{ display: none; }}
        header[data-testid="stHeader"] {{ display: none; }}
        #MainMenu {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}
        
        /* WIDGET STYLING */
        .stButton button {{
            background: {c['accent']} !important;
            color: white !important;
            border: none !important;
            width: 100%;
            border-radius: 10px;
        }}
        
    </style>
""", unsafe_allow_html=True)

# --- 4. LOGIC ---
def toggle_sidebar(): st.session_state.sidebar_open = not st.session_state.sidebar_open
def toggle_theme(): st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'

@st.cache_data(ttl=60)
def get_user_data(username):
    try:
        url = f"{SUPABASE_URL}/rest/v1/users?username=eq.{username}&select=*"
        res = requests.get(url, headers=HEADERS)
        return res.json()[0] if res.status_code == 200 and res.json() else None
    except: return None

def get_ai_response(prompt, history, expert):
    # Dummy Response for UI Testing (Connect your Logic Here)
    return "ئەمە وەڵامێکی تاقیکارییە. دیزاینەکە ئێستا تەواو ڕێکخراوە.", 10

# --- 5. APP LAYOUT ---

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    # --- LOGIN PAGE ---
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown(f"<br><br><h2 style='text-align:center; color:{c['text']}'>چوونەژوورەوە</h2>", unsafe_allow_html=True)
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            user = get_user_data(u)
            if user and str(user['password']) == str(p):
                st.session_state.logged_in = True
                st.session_state.username = u
                st.session_state.user_info = user
                st.rerun()
            else: st.error("هەڵەیە")
else:
    # --- MAIN DASHBOARD ---
    
    # 1. SIDEBAR CONTENT (Rendered inside a hidden container but styled via CSS)
    with st.container():
        st.markdown(f"""
            <div class="custom-sidebar">
                <div style="text-align:center; margin-bottom:20px;">
                    <h2 style="margin:0; color:{c['text']}">🦁 Zirak AI</h2>
                    <p style="color:{c['text']}; opacity:0.7; font-size:12px;">{st.session_state.username}</p>
                </div>
        """, unsafe_allow_html=True)
        
        # Sidebar Widgets (They need to be hacked into the sidebar div via CSS order, but simpler is to use Streamlit columns here)
        # NOTE: Streamlit widgets cannot be strictly inside HTML strings.
        # We use the CSS positioning to make the "Sidebar Area" visible.
        # The buttons below are technically in the main flow but positioned absolute/fixed via CSS logic?
        # NO, for stability, we will use a "Control Panel" in the sidebar area using `st.sidebar` logic REIMAGINED.
        
        # SINCE WE HID THE NATIVE SIDEBAR, WE MUST BUILD A CUSTOM ONE WITH NATIVE WIDGETS
        # TRICK: We create a 2-column layout. Col 1 is empty (spacer). Col 2 is content.
        # But `st.columns` doesn't support fixed positioning.
        
        # SOLUTION FOR "WORKING" SIDEBAR BUTTONS:
        # We use a container that CSS moves to the right.
        
        with st.container():
            st.markdown('<div style="position:fixed; top:80px; right:' + ('20px' if st.session_state.sidebar_open else '-300px') + '; width:260px; z-index:1001; transition:right 0.3s; direction:rtl;">', unsafe_allow_html=True)
            
            st.markdown(f"<h4 style='color:{c['text']}'>بەشەکان</h4>", unsafe_allow_html=True)
            
            expert = st.radio(" ", ["🧠 مێشکی کۆرسەکە", "🗣️ وەرگێڕ", "📐 حاسیبە", "✍️ ستراتیژیست", "📊 باڵانس"], label_visibility="collapsed")
            st.session_state.expert = expert
            
            st.markdown("---")
            if st.button("چوونە دەرەوە"):
                st.session_state.logged_in = False
                st.rerun()
                
            st.markdown('</div>', unsafe_allow_html=True)
            
        st.markdown("</div>", unsafe_allow_html=True) # Close sidebar div

    # 2. MAIN CONTENT WRAPPER
    st.markdown('<div class="main-content-wrapper">', unsafe_allow_html=True)
    
    # Top Bar (Menu & Theme)
    c_menu, c_title, c_theme = st.columns([1, 10, 1])
    with c_menu:
        if st.button("☰", key="menu"): toggle_sidebar(); st.rerun()
    with c_title:
        st.markdown(f"<h3 style='margin:0; text-align:center; color:{c['text']}'>{st.session_state.expert}</h3>", unsafe_allow_html=True)
    with c_theme:
        if st.button("🌓", key="theme"): toggle_theme(); st.rerun()

    # Chat Area
    st.markdown("---")
    
    # 3. UPLOAD SECTION (The missing part)
    # Using an Expander for clean UI
    with st.expander("📎 زیادکردنی فایل و وێنە (Upload)", expanded=False):
        uc1, uc2 = st.columns(2)
        with uc1:
            img = st.file_uploader("وێنە یان PDF", type=['png','jpg','pdf'])
        with uc2:
            cam = st.camera_input("کامێرا")
            
        if img or cam:
            st.success("✅ فایل ئامادەیە بۆ ناردن")

    # Chat History
    if "messages" not in st.session_state: st.session_state.messages = []
    
    for m in st.session_state.messages:
        with st.chat_message(m["role"], avatar="🦁" if m["role"]=="assistant" else "👤"):
            st.markdown(m["content"])

    # Chat Input
    if prompt := st.chat_input("پرسیارەکەت بنووسە..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Add file note
        if img or cam: prompt += " [Attached File]"
        
        st.rerun() # Refresh to show user message instantly
        
        # (AI Logic would go here in background)

    st.markdown('</div>', unsafe_allow_html=True)