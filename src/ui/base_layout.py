import streamlit as st


# =========================
# HOME BACKGROUND
# =========================
def style_background_home():
    st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(135deg, #5865F2, #8A9BFF) !important;
        }

        .stApp div[data-testid="stColumn"] {
            background-color: #E0E3FF !important;
            padding: 2.5rem !important;
            border-radius: 2rem !important;
            box-shadow: 0px 10px 30px rgba(0,0,0,0.1);
        }
        </style>
    """, unsafe_allow_html=True)


# =========================
# DASHBOARD BACKGROUND
# =========================
def style_background_dashboard():
    st.markdown("""
        <style>
        .stApp {
            background: #E0E3FF !important;
        }
        </style>
    """, unsafe_allow_html=True)


# =========================
# BASE UI STYLE
# =========================
def style_base_layout():
    st.markdown("""
        <style>

        @import url('https://fonts.googleapis.com/css2?family=Climate+Crisis&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@100..900&display=swap');

        /* Hide Streamlit UI */
        #MainMenu, footer, header {
            visibility: hidden;
        }

        .block-container {
            padding-top: 1.5rem !important;
        }

        /* HEADINGS */
        h1 {
            font-family: 'Climate Crisis', sans-serif !important;
            font-size: 3.5rem !important;
            line-height: 1.1 !important;
            margin-bottom: 0rem !important;
        }

        h2 {
            font-family: 'Climate Crisis', sans-serif !important;
            font-size: 2rem !important;
            line-height: 1 !important;
            margin-bottom: 0rem !important;
        }

        h3, h4, p {
            font-family: 'Outfit', sans-serif !important;
        }

        /* BUTTONS */
        .stButton > button {
            border-radius: 1.5rem !important;
            background-color: #5865F2 !important;
            color: white !important;
            padding: 10px 20px !important;
            border: none !important;
            transition: all 0.25s ease-in-out !important;
        }

        .stButton > button:hover {
            transform: scale(1.05);
            background-color: #4752c4 !important;
        }

        /* SECONDARY BUTTON */
        button[kind="secondary"] {
            background-color: #EB459E !important;
        }

        /* TERTIARY BUTTON */
        button[kind="tertiary"] {
            background-color: black !important;
        }

        </style>
    """, unsafe_allow_html=True)