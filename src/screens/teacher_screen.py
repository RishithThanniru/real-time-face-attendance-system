import streamlit as st

from src.ui.base_layout import style_background_dashboard, style_base_layout
from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from src.components.subject_card import subject_card
from src.database.db import check_teacher_exists, create_teacher, teacher_login, get_teacher_subjects, get_attendance_for_teacher
from src.components.dialog_create_subject import create_subject_dialog
from src.components.dialog_share_subject import share_subject_dialog
from src.components.dialog_add_photo import add_photos_dialog

from src.pipelines.face_pipeline import predict_attendance
from src.components.dialog_attendance_results import attendance_result_dialog
import numpy as np

from datetime import datetime
import pandas as pd

from src.database.config import supabase
from src.components.dialog_voice_attendance import voice_attendance_dialog


# =========================
# MAIN
# =========================
def teacher_screen():
    style_background_dashboard()
    style_base_layout()

    if "teacher_data" in st.session_state:
        teacher_dashboard()
    elif 'teacher_login_type' not in st.session_state or st.session_state.teacher_login_type == "login":
        teacher_screen_login()
    elif st.session_state.teacher_login_type == "register":
        teacher_screen_register()


# =========================
# DASHBOARD
# =========================
def teacher_dashboard():
    teacher_data = st.session_state.teacher_data

    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')

    with c1:
        header_dashboard()

    with c2:
        st.subheader(f"Welcome, {teacher_data['name']}")

        if st.button("Logout", type='secondary', key='loginbackbtn'):
            st.session_state.clear()
            st.rerun()

    st.space()

    if "current_teacher_tab" not in st.session_state:
        st.session_state.current_teacher_tab = 'take_attendance'

    tab1, tab2, tab3 = st.columns(3)

    with tab1:
        if st.button('Take Attendance'):
            st.session_state.current_teacher_tab = 'take_attendance'

    with tab2:
        if st.button('Manage Subjects'):
            st.session_state.current_teacher_tab = 'manage_subjects'

    with tab3:
        if st.button('Attendance Records'):
            st.session_state.current_teacher_tab = 'attendance_records'

    st.divider()

    if st.session_state.current_teacher_tab == "take_attendance":
        teacher_tab_take_attendance()

    elif st.session_state.current_teacher_tab == "manage_subjects":
        teacher_tab_manage_subjects()

    elif st.session_state.current_teacher_tab == "attendance_records":
        teacher_tab_attendance_records()

    footer_dashboard()


# =========================
# TAKE ATTENDANCE
# =========================
def teacher_tab_take_attendance():
    teacher_id = st.session_state.teacher_data['id']   # FIX

    st.header('Take AI Attendance')

    if 'attendance_images' not in st.session_state:
        st.session_state.attendance_images = []

    subjects = get_teacher_subjects(teacher_id)

    if not subjects:
        st.warning('Create subject first')
        return

    subject_options = {f"{s['name']} - {s['subject_code']}": s['id'] for s in subjects}  # FIX

    selected_label = st.selectbox('Select Subject', list(subject_options.keys()))
    selected_subject_id = subject_options[selected_label]

    if st.button('Add Photos'):
        add_photos_dialog()

    if st.session_state.attendance_images:
        for img in st.session_state.attendance_images:
            st.image(img)

    if st.button('Run Face Analysis'):

        all_detected = {}

        for idx, img in enumerate(st.session_state.attendance_images):
            img_np = np.array(img.convert('RGB'))
            detected, _, _ = predict_attendance(img_np)

            for sid in detected:
                all_detected[int(sid)] = True

        enrolled = supabase.table('subject_students') \
            .select("*, students(*)") \
            .eq('subject_id', selected_subject_id) \
            .execute().data or []

        results, logs = [], []
        now = datetime.now().isoformat()

        for node in enrolled:
            student = node['students']
            sid = student['id']   # FIX

            present = sid in all_detected

            results.append({
                "Name": student['name'],
                "ID": sid,
                "Status": "Present" if present else "Absent"
            })

            logs.append({
                'student_id': sid,
                'subject_id': selected_subject_id,
                'timestamp': now,
                'is_present': present
            })

        attendance_result_dialog(pd.DataFrame(results), logs)

    if st.button('Voice Attendance'):
        voice_attendance_dialog(selected_subject_id)


# =========================
# SUBJECTS
# =========================
def teacher_tab_manage_subjects():
    teacher_id = st.session_state.teacher_data['id']   # FIX

    if st.button('Create Subject'):
        create_subject_dialog(teacher_id)

    subjects = get_teacher_subjects(teacher_id)

    if subjects:
        for sub in subjects:

            def share_btn():
                if st.button(f"Share {sub['name']}"):
                    share_subject_dialog(sub['name'], sub['subject_code'])

            subject_card(
                name=sub['name'],
                code=sub['subject_code'],
                section=sub['section'],
                stats=[
                    ("Students", sub['total_students']),
                    ("Classes", sub['total_classes'])
                ],
                footer_callback=share_btn
            )
    else:
        st.info("No subjects")


# =========================
# RECORDS
# =========================
def teacher_tab_attendance_records():
    teacher_id = st.session_state.teacher_data['id']   # FIX

    records = get_attendance_for_teacher(teacher_id)

    if not records:
        return

    df = pd.DataFrame(records)
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
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')

    if st.button("Login"):
        if login_teacher(username, password):
            st.rerun()


# =========================
# REGISTER
# =========================
def teacher_screen_register():
    name = st.text_input("Name")
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')

    if st.button("Register"):
        if not check_teacher_exists(username):
            create_teacher(username, password, name)
            st.session_state.teacher_login_type = "login"
            st.rerun()