import streamlit as st
import requests
import json
import time

# --- 1. CONFIG & STATE ---
st.set_page_config(page_title="Zirak AI", page_icon="🔹", layout="wide", initial_sidebar_state="collapsed")

# Initialize Session State
if 'theme' not in st.session_state: st.session_state.theme = 'light'
if 'sidebar_open' not in st.session_state: st.session_state.sidebar_open = True # Desktop default
if 'mobile_check' not in st.session_state: st.session_state.mobile_check = False

# --- 2. THEME ENGINE & CSS ---
def get_theme_colors():
    if st.session_state.theme == 'light':
        return {
            "bg": "#ffffff",
            "text": "#1e293b",
            "sidebar_bg": "#f8fafc",
            "sidebar_text": "#334155",
            "input_bg": "#f1f5f9",
            "input_border": "#e2e8f0",
            "accent": "#2563eb", # Professional Blue
            "accent_hover": "#1d4ed8",
            "card_bg": "#ffffff",
            "shadow": "rgba(0,0,0,0.05)"
        }
    else:
        return {
            "bg": "#0f172a",
            "text": "#f1f5f9",
            "sidebar_bg": "#1e293b",
            "sidebar_text": "#e2e8f0",
            "input_bg": "#334155",
            "input_border": "#475569",
            "accent": "#3b82f6", # Lighter Blue for Dark Mode
            "accent_hover": "#60a5fa",
            "card_bg": "#1e293b",
            "shadow": "rgba(0,0,0,0.3)"
        }

colors = get_theme_colors()

# Sidebar Animation Logic (RTL: Negative value moves left, Positive moves right)
# We want it on the RIGHT side. Closed = TranslateX(100%). Open = TranslateX(0).
sidebar_pos = "0px" if st.session_state.sidebar_open else "320px" # Slide out to right

st.markdown(f"""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@400;500;700;900&display=swap');
        
        * {{ font-family: 'Noto Sans Arabic', sans-serif !important; transition: background-color 0.3s, color 0.3s; }}
        
        /* Main App Background */
        .stApp {{
            background-color: {colors['bg']};
            color: {colors['text']};
        }}

        /* --- CUSTOM HEADER (Fixed Top) --- */
        .custom-header {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 70px;
            background-color: {colors['bg']};
            border-bottom: 1px solid {colors['input_border']};
            z-index: 1000;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 20px;
            direction: rtl;
        }}
        
        .header-title {{
            font-weight: 900;
            font-size: 22px;
            color: {colors['accent']};
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        /* --- CUSTOM SIDEBAR (Floating) --- */
        .custom-sidebar {{
            position: fixed;
            top: 70px; /* Below Header */
            right: 0;
            width: 300px;
            height: calc(100vh - 70px);
            background-color: {colors['sidebar_bg']};
            border-left: 1px solid {colors['input_border']};
            z-index: 999;
            transform: translateX({sidebar_pos});
            transition: transform 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
            padding: 20px;
            direction: rtl;
            overflow-y: auto;
            box-shadow: -5px 0 15px {colors['shadow']};
        }}

        /* --- CONTENT AREA ADJUSTMENT --- */
        .main-content {{
            margin-top: 80px; /* Space for header */
            margin-right: { "300px" if st.session_state.sidebar_open else "0px" };
            transition: margin-right 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
            padding: 20px;
        }}
        
        /* Mobile Adjustment */
        @media (max-width: 768px) {{
            .main-content {{ margin-right: 0px !important; }} /* Sidebar becomes overlay on mobile */
        }}

        /* --- WIDGET STYLING --- */
        /* Buttons */
        .stButton > button {{
            background-color: {colors['accent']} !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 10px 20px !important;
            font-weight: bold !important;
        }}
        
        /* Inputs */
        .stTextInput input, .stSelectbox div[data-baseweb="select"] {{
            background-color: {colors['input_bg']} !important;
            border: 1px solid {colors['input_border']} !important;
            color: {colors['text']} !important;
            border-radius: 12px !important;
        }}
        
        /* Chat Messages */
        .stChatMessage {{
            background-color: {colors['card_bg']} !important;
            border: 1px solid {colors['input_border']} !important;
            border-radius: 16px !important;
            box-shadow: 0 2px 5px {colors['shadow']} !important;
        }}
        
        /* Navigation Buttons Styling */
        .nav-btn {{
            width: 100%;
            text-align: right;
            background: transparent;
            border: none;
            padding: 12px 15px;
            color: {colors['sidebar_text']};
            border-radius: 10px;
            cursor: pointer;
            font-size: 16px;
            display: flex;
            align-items: center;
            gap: 12px;
            transition: all 0.2s;
            margin-bottom: 5px;
        }}
        .nav-btn:hover {{
            background-color: {colors['input_bg']};
            color: {colors['accent']};
        }}
        .nav-btn.active {{
            background-color: {colors['accent']}20; /* 20% opacity */
            color: {colors['accent']};
            font-weight: bold;
            border-right: 4px solid {colors['accent']};
        }}

        /* Hide Default Streamlit Elements */
        [data-testid="stSidebar"] {{ display: none; }}
        header[data-testid="stHeader"] {{ display: none; }}
        #MainMenu {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}
        
    </style>
""", unsafe_allow_html=True)

# --- 3. LOGIC FUNCTIONS ---
def toggle_theme():
    st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'

def toggle_sidebar():
    st.session_state.sidebar_open = not st.session_state.sidebar_open

# Mocking DB functions for design preview (Replace with your Supabase calls)
def get_user_data(u): return {'password': '123', 'token_limit': 1000, 'used_tokens': 200, 'plan': 'Pro'}
def get_ai_response(p, h, e): return "ئەمە وەڵامێکی تاقیکارییە بۆ دیزاینەکە.", 10

# --- 4. HEADER UI (Custom HTML/Python Mix) ---
col_h1, col_h2, col_h3 = st.columns([1, 6, 1])

# Header Container
with st.container():
    # We use columns to simulate the header layout inside the Streamlit flow
    # But visually we pushed it to top via CSS ".custom-header"
    pass 

# Since we hid the default header, we build controls here
# This part is tricky in Streamlit. We'll use a container that acts as the control bar.
# But for the requested "Sidebar Animation", we need to render the buttons.

# --- 5. MAIN APP LAYOUT ---

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    # --- LOGIN SCREEN (Centered & Adaptive) ---
    st.markdown("<br><br>", unsafe_allow_html=True)
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
        
        u = st.text_input("نازناو", placeholder="Username")
        p = st.text_input("وشەی نهێنی", type="password", placeholder="••••••••")
        
        if st.button("چوونەژوورەوە", use_container_width=True):
            if u == "admin" and p == "123": # Mock Login
                st.session_state.logged_in = True
                st.session_state.username = u
                st.rerun()
            else: st.error("زانیاری هەڵەیە")
            
    # Theme Toggle for Login
    st.markdown(f"""
        <div style="position:fixed; bottom:20px; left:20px;">
            <button onclick="document.dispatchEvent(new KeyboardEvent('keydown', {{key: 't', ctrlKey: true}}))" style="background:none; border:none; font-size:24px; color:{colors['sidebar_text']}; cursor:pointer;">
                <i class="fa-solid {'fa-moon' if st.session_state.theme=='light' else 'fa-sun'}"></i>
            </button>
        </div>
    """, unsafe_allow_html=True)
    
    # Hidden button to trigger theme toggle via script if needed, or just use a streamlit button
    c_t1, c_t2 = st.columns([10, 1])
    with c_t2:
        if st.button("🌓", key="login_theme"): toggle_theme(); st.rerun()

else:
    # --- LOGGED IN AREA ---
    
    # 1. THE HEADER
    st.markdown(f"""
        <div class="custom-header">
            <div class="header-title">
                <i class="fa-solid fa-layer-group"></i>
                Zirak AI
            </div>
            <div>
                </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Header Buttons (Invisible overlay or standard buttons positioned absolutely? 
    # Streamlit buttons are hard to place in custom HTML. We use columns at the very top)
    
    h_col1, h_col2, h_col3 = st.columns([1, 8, 1])
    with h_col1:
        # Menu Toggle Button
        btn_icon = "fa-bars" if not st.session_state.sidebar_open else "fa-xmark"
        if st.button("☰", key="menu_toggle"): 
            toggle_sidebar()
            st.rerun()
            
    with h_col3:
        # Theme Toggle Button
        theme_icon = "🌙" if st.session_state.theme == 'light' else "☀️"
        if st.button(theme_icon, key="theme_toggle"): 
            toggle_theme()
            st.rerun()

    # 2. THE SIDEBAR (Custom HTML Rendered)
    if 'expert' not in st.session_state: st.session_state.expert = "🧠 مێشکی کۆرسەکە"
    
    # We create a list of options. Using buttons for navigation.
    with st.container():
        # This HTML is for visual representation, the logic is handled by Streamlit buttons hidden or styled.
        # Ideally, we put the buttons inside a container that IS the sidebar visually.
        
        # NOTE: Streamlit renders widgets sequentially. To put widgets in the "sidebar div", 
        # we can't easily. So we will simulate the sidebar content using a standard column 
        # BUT we won't use it because it pushes content.
        
        # SOLUTION: We will render the sidebar menu using pure HTML/JS for visual 
        # and simple Streamlit radio for actual logic if we want simplicity, 
        # OR we use the "Dialog" approach.
        
        # Let's stick to a robust approach: Standard Streamlit widgets but we inject them into the sidebar container via CSS? No.
        
        # We will render the MENU ITEMS inside the Sidebar Div manually.
        menu_items = [
            {"icon": "fa-brain", "label": "مێشکی کۆرسەکە"},
            {"icon": "fa-language", "label": "وەرگێڕی بازرگانی"},
            {"icon": "fa-calculator", "label": "حاسیبەی لۆجستی"},
            {"icon": "fa-pen-nib", "label": "ستراتیژیستی ناوەڕۆک"},
            {"icon": "fa-chart-pie", "label": "ڕاپۆرتی نهێنی"},
            {"icon": "fa-wallet", "label": "باڵانسی من"},
        ]
        
        # Render Sidebar Content
        sidebar_html = f"""
        <div class="custom-sidebar">
            <div style="margin-bottom: 30px; padding: 10px; background: {colors['input_bg']}; border-radius: 12px; display: flex; align-items: center; gap: 10px;">
                <div style="width: 40px; height: 40px; background: {colors['accent']}; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold;">
                    {st.session_state.username[0].upper()}
                </div>
                <div>
                    <div style="font-weight: bold; font-size: 14px;">{st.session_state.username}</div>
                    <div style="font-size: 11px; opacity: 0.7;">Pro Plan</div>
                </div>
            </div>
            
            <div style="display: flex; flex-direction: column; gap: 5px;">
        """
        
        # We can't put streamlit buttons inside an f-string HTML.
        # So we use a creative layout:
        # The sidebar container is purely visual via CSS above.
        # We place a vertical column of buttons on the screen, and use CSS to move that column INTO the sidebar area.
        pass

    # --- 3. IMPLEMENTING THE NAVIGATION LOGIC ---
    # We place a container that CSS will move into the fixed sidebar position
    with st.container():
        st.markdown('<div class="sidebar-logic-container">', unsafe_allow_html=True)
        # We inject CSS to move this specific container into the .custom-sidebar area
        st.markdown(f"""
        <style>
            div[data-testid="stVerticalBlock"] > div:has(div.sidebar-buttons) {{
                position: fixed;
                top: 180px;
                right: { "20px" if st.session_state.sidebar_open else "-300px" };
                width: 260px;
                z-index: 1001;
                transition: right 0.4s;
                direction: rtl;
            }}
        </style>
        <div class="sidebar-buttons"></div>
        """, unsafe_allow_html=True)
        
        # Navigation Buttons
        for item in menu_items:
            label = item['label']
            icon_class = item['icon']
            is_active = st.session_state.expert == label
            
            # Using columns to create the icon + button effect
            bt_col1, bt_col2 = st.columns([1, 5])
            with bt_col1:
                st.markdown(f'<div style="text-align:center; padding-top:8px; color:{colors["accent"] if is_active else colors["sidebar_text"]};"><i class="fa-solid {icon_class}"></i></div>', unsafe_allow_html=True)
            with bt_col2:
                if st.button(label, key=f"nav_{label}", use_container_width=True):
                    st.session_state.expert = label
                    if st.session_state.mobile_check: # Close sidebar on mobile after click
                        st.session_state.sidebar_open = False
                    st.rerun()
        
        st.markdown("<hr style='opacity:0.1'>", unsafe_allow_html=True)
        if st.button("چوونە دەرەوە", key="logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
            
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 4. MAIN CONTENT ---
    # CSS puts this in the correct place
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
    expert = st.session_state.expert
    
    # Header for Chat Area
    st.markdown(f"""
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:20px;">
            <h2 style="margin:0; color:{colors['text']};">{expert}</h2>
            <span style="background:{colors['accent']}20; color:{colors['accent']}; padding:2px 10px; border-radius:20px; font-size:12px; font-weight:bold;">Active</span>
        </div>
    """, unsafe_allow_html=True)

    # --- CHAT LOGIC ---
    if expert == "📊 باڵانسی من":
        c1, c2 = st.columns(2)
        c1.metric("تۆکنی ماوە", "85,000")
        c2.metric("پاکێج", "Pro")
        st.progress(0.2)
    else:
        # Chat Messages
        if "messages" not in st.session_state: st.session_state.messages = []
        
        for m in st.session_state.messages:
            with st.chat_message(m["role"], avatar="🦁" if m["role"]=="assistant" else "👤"):
                st.markdown(m["content"])

        # Chat Input
        if prompt := st.chat_input("پرسیارەکەت بنووسە..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            # (Add your AI Logic here)
            st.session_state.messages.append({"role": "assistant", "content": "وەڵامێکی نموونەیی..."})
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)