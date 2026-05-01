import streamlit as st
from datetime import datetime
import numpy as np
import pandas as pd

from src.ui.base_layout import style_background_dashboard, style_base_layout
from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from src.components.subject_card import subject_card

from src.database.db import (
    check_teacher_exists,
    create_teacher,
    teacher_login,
    get_teacher_subjects,
    get_attendance_for_teacher
)

from src.components.dialog_create_subject import create_subject_dialog
from src.components.dialog_add_photo import add_photos_dialog
from src.components.dialog_attendance_results import attendance_result_dialog

from src.pipelines.face_pipeline import predict_attendance
from src.database.config import supabase


# =========================
# MAIN SCREEN
# =========================
def teacher_screen():
    style_background_dashboard()
    style_base_layout()

    if "teacher_login_type" not in st.session_state:
        st.session_state.teacher_login_type = "login"

    if "teacher_data" in st.session_state:
        teacher_dashboard()
    elif st.session_state.teacher_login_type == "login":
        teacher_screen_login()
    else:
        teacher_screen_register()


# =========================
# DASHBOARD
# =========================
def teacher_dashboard():
    teacher_data = st.session_state.teacher_data
    teacher_id = teacher_data.get("id")

    if not teacher_id:
        st.error("❌ Teacher not logged in properly")
        st.stop()

    c1, c2 = st.columns(2)

    with c1:
        header_dashboard()

    with c2:
        st.subheader(f"Welcome, {teacher_data['name']}")
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()

    if "current_teacher_tab" not in st.session_state:
        st.session_state.current_teacher_tab = "take_attendance"

    tab1, tab2, tab3 = st.columns(3)

    if tab1.button("Take Attendance"):
        st.session_state.current_teacher_tab = "take_attendance"

    if tab2.button("Manage Subjects"):
        st.session_state.current_teacher_tab = "manage_subjects"

    if tab3.button("Attendance Records"):
        st.session_state.current_teacher_tab = "attendance_records"

    st.divider()

    if st.session_state.current_teacher_tab == "take_attendance":
        teacher_tab_take_attendance(teacher_id)

    elif st.session_state.current_teacher_tab == "manage_subjects":
        teacher_tab_manage_subjects(teacher_id)

    elif st.session_state.current_teacher_tab == "attendance_records":
        teacher_tab_attendance_records(teacher_id)

    footer_dashboard()


# =========================
# TAKE ATTENDANCE
# =========================
def teacher_tab_take_attendance(teacher_id):
    st.header("Take AI Attendance")

    subjects = get_teacher_subjects(teacher_id)

    if not subjects:
        st.warning("No subjects found")
        return

    subject_options = {s["name"]: s["id"] for s in subjects}
    selected_subject = st.selectbox("Select Subject", subject_options.keys())
    selected_subject_id = subject_options[selected_subject]

    if st.button("Add Photos"):
        add_photos_dialog()

    if "attendance_images" not in st.session_state:
        st.session_state.attendance_images = []

    for img in st.session_state.attendance_images:
        st.image(img)

    if st.button("Run Face Analysis"):
        all_detected = {}

        for img in st.session_state.attendance_images:
            img_np = np.array(img.convert("RGB"))
            detected, _, _ = predict_attendance(img_np)

            for sid in detected.keys():
                all_detected[int(sid)] = True

        enrolled = supabase.table("subject_students") \
            .select("*") \
            .eq("subject_id", selected_subject_id) \
            .execute().data or []

        results = []
        logs = []

        now = datetime.now().isoformat()

        for e in enrolled:
            sid = e["student_id"]
            present = sid in all_detected

            results.append({
                "Student ID": sid,
                "Status": "Present" if present else "Absent"
            })

            logs.append({
                "student_id": sid,
                "subject_id": selected_subject_id,
                "timestamp": now,
                "is_present": present
            })

        attendance_result_dialog(pd.DataFrame(results), logs)


# =========================
# MANAGE SUBJECTS
# =========================
def teacher_tab_manage_subjects(teacher_id):
    st.header("Manage Subjects")

    if st.button("Create Subject"):
        create_subject_dialog(teacher_id)

    subjects = get_teacher_subjects(teacher_id)

    if not subjects:
        st.info("No subjects found")
        return

    for sub in subjects:
        subject_card(
            name=sub["name"],
            code=sub["subject_code"],
            section=sub["section"],
            stats=[
                ("Students", sub["total_students"]),
                ("Classes", sub["total_classes"]),
            ]
        )


# =========================
# ATTENDANCE RECORDS
# =========================
def teacher_tab_attendance_records(teacher_id):
    st.header("Attendance Records")

    records = get_attendance_for_teacher(teacher_id)

    if not records:
        st.info("No records found")
        return

    df = pd.DataFrame(records)

    if "timestamp" in df.columns:
        df["Time"] = pd.to_datetime(df["timestamp"])

    st.dataframe(df)


# =========================
# LOGIN
# =========================
def login_teacher(username, password):
    teacher = teacher_login(username, password)

    if teacher:
        st.session_state.teacher_data = teacher
        return True
    return False


def teacher_screen_login():
    st.markdown("<h1 style='text-align:center;'>Login</h1>", unsafe_allow_html=True)

    st.image("https://i.ibb.co/4r5X1FY/apnacollege.png", width=90)

    if "show_password" not in st.session_state:
        st.session_state.show_password = False

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        username = st.text_input("Username")

        p1, p2 = st.columns([10, 1])

        with p1:
            password = st.text_input(
                "Password",
                type="default" if st.session_state.show_password else "password"
            )

        with p2:
            if st.button("👁️"):
                st.session_state.show_password = not st.session_state.show_password
                st.rerun()

        st.markdown("###")

        c1, c2 = st.columns(2)

        with c1:
            if st.button("Login", use_container_width=True):
                if login_teacher(username, password):
                    st.success("Logged in")
                    st.rerun()
                else:
                    st.error("Invalid credentials")

        with c2:
            if st.button("Register", use_container_width=True):
                st.session_state.teacher_login_type = "register"
                st.rerun()


# =========================
# REGISTER
# =========================
def teacher_screen_register():
    st.markdown("<h1 style='text-align:center;'>Register</h1>", unsafe_allow_html=True)

    st.image("https://i.ibb.co/4r5X1FY/apnacollege.png", width=90)

    if "show_password" not in st.session_state:
        st.session_state.show_password = False

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        username = st.text_input("Username")
        name = st.text_input("Name")

        p1, p2 = st.columns([10, 1])

        with p1:
            password = st.text_input(
                "Password",
                type="default" if st.session_state.show_password else "password"
            )

        with p2:
            if st.button("👁️ "):
                st.session_state.show_password = not st.session_state.show_password
                st.rerun()

        st.markdown("###")

        c1, c2 = st.columns(2)

        with c1:
            if st.button("Create Account", use_container_width=True):
                if check_teacher_exists(username):
                    st.error("Username already exists")
                else:
                    create_teacher(username, password, name)
                    st.success("Account created!")
                    st.session_state.teacher_login_type = "login"
                    st.rerun()

        with c2:
            if st.button("Back to Login", use_container_width=True):
                st.session_state.teacher_login_type = "login"
                st.rerun()