import streamlit as st
from src.ui.base_layout import style_background_dashboard, style_base_layout
from src.components.header import header_dashboard
from src.components.footer import footer_dashboard

from src.database.db import (
    check_teacher_exists,
    create_teacher,
    teacher_login,
    get_teacher_subjects
)

from src.components.dialog_create_subject import create_subject_dialog
from src.components.subject_card import subject_card


# =========================
# MAIN ENTRY
# =========================
def teacher_screen():
    style_background_dashboard()
    style_base_layout()

    if "teacher_data" in st.session_state:
        teacher_dashboard()
    else:
        teacher_auth()


# =========================
# LOGIN / REGISTER
# =========================
def teacher_auth():
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"

    if st.session_state.auth_mode == "login":
        teacher_login_ui()
    else:
        teacher_register_ui()


def teacher_login_ui():
    st.markdown("<h1 style='text-align:center;'>Teacher Login</h1>", unsafe_allow_html=True)

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        teacher = teacher_login(username, password)

        if teacher:
            st.session_state.teacher_data = teacher
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid credentials")

    if st.button("Go to Register"):
        st.session_state.auth_mode = "register"
        st.rerun()


def teacher_register_ui():
    st.markdown("<h1 style='text-align:center;'>Teacher Register</h1>", unsafe_allow_html=True)

    name = st.text_input("Name")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Create Account"):
        if check_teacher_exists(username):
            st.error("Username already exists")
        else:
            create_teacher(username, password, name)
            st.success("Account created")
            st.session_state.auth_mode = "login"
            st.rerun()

    if st.button("Back to Login"):
        st.session_state.auth_mode = "login"
        st.rerun()


# =========================
# DASHBOARD
# =========================
def teacher_dashboard():
    teacher = st.session_state.teacher_data
    teacher_id = teacher.get("id")

    c1, c2 = st.columns(2)

    with c1:
        header_dashboard()

    with c2:
        st.subheader(f"Welcome, {teacher.get('name')}")
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()

    st.divider()

    if st.button("Create Subject"):
        create_subject_dialog(teacher_id)

    subjects = get_teacher_subjects(teacher_id) or []

    if not subjects:
        st.info("No subjects found")
        return

    for sub in subjects:
        subject_card(
            name=sub.get("name"),
            code=sub.get("subject_code"),
            section=sub.get("section"),
            stats=[
                ("Students", sub.get("total_students", 0)),
                ("Classes", sub.get("total_classes", 0)),
            ],
        )

    footer_dashboard()