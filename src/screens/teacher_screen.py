import streamlit as st
from src.ui.base_layout import style_background_dashboard, style_base_layout
from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from PIL import Image
import numpy as np
from src.pipelines.face_pipeline import predict_attendance, get_face_embeddings, train_classifier
from src.pipelines.voice_pipeline import get_voice_embedding
from src.database.db import get_all_students, create_student, get_student_subjects, get_student_attendance, unenroll_student_to_subject
import time

from src.components.dialog_enroll import enroll_dialog
from src.components.subject_card import subject_card


# =========================
# DASHBOARD
# =========================
def student_dashboard():
    student_data = st.session_state.student_data
    student_id = student_data.get("id")  # ✅ FIX

    c1, c2 = st.columns(2)
    with c1:
        header_dashboard()
    with c2:
        st.subheader(f"Welcome, {student_data['name']}")
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()

    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        st.header("Your Enrolled Subjects")
    with c2:
        if st.button("Enroll in Subject"):
            enroll_dialog()

    with st.spinner("Loading subjects..."):
        subjects = get_student_subjects(student_id) or []
        logs = get_student_attendance(student_id) or []

    stats_map = {}

    for log in logs:
        sid = log.get("subject_id")

        if sid not in stats_map:
            stats_map[sid] = {"total": 0, "attended": 0}

        stats_map[sid]["total"] += 1

        if log.get("is_present"):
            stats_map[sid]["attended"] += 1

    cols = st.columns(2)

    for i, sub_node in enumerate(subjects):
        sub = sub_node.get("subjects", {})
        sid = sub.get("id")  # ✅ FIX

        stats = stats_map.get(sid, {"total": 0, "attended": 0})

        def unenroll_button():
            if st.button("Unenroll"):
                unenroll_student_to_subject(student_id, sid)
                st.toast(f"Unenrolled from {sub.get('name')} successfully!")
                st.rerun()

        with cols[i % 2]:
            subject_card(
                name=sub.get("name"),
                code=sub.get("subject_code"),
                section=sub.get("section"),
                stats=[
                    ("📅", "Total", stats["total"]),
                    ("✅", "Attended", stats["attended"]),
                ],
                footer_callback=unenroll_button,
            )

    footer_dashboard()


# =========================
# MAIN SCREEN
# =========================
def student_screen():
    style_background_dashboard()
    style_base_layout()

    if "student_data" in st.session_state:
        student_dashboard()
        return

    c1, c2 = st.columns(2)
    with c1:
        header_dashboard()
    with c2:
        if st.button("Go back"):
            st.session_state.clear()
            st.rerun()

    st.header("Login using FaceID")

    photo_source = st.camera_input("Capture your face")

    show_registration = False

    if photo_source:
        img = np.array(Image.open(photo_source))

        with st.spinner("Scanning..."):
            detected, all_ids, num_faces = predict_attendance(img)

            if num_faces == 0:
                st.warning("No face found")

            elif num_faces > 1:
                st.warning("Multiple faces detected")

            else:
                if detected:
                    student_id = list(detected.keys())[0]

                    students = get_all_students() or []
                    student = next((s for s in students if s.get("id") == student_id), None)

                    if student:
                        st.session_state.student_data = student
                        st.success(f"Welcome {student['name']}")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.info("New student detected")
                    show_registration = True

    # =========================
    # REGISTER
    # =========================
    if show_registration:
        st.subheader("Register")

        new_name = st.text_input("Enter your name")

        audio_data = None
        try:
            audio_data = st.audio_input("Record voice")
        except:
            pass

        if st.button("Create Account"):
            if not new_name:
                st.warning("Enter name")
                return

            img = np.array(Image.open(photo_source))
            encodings = get_face_embeddings(img)

            if not encodings:
                st.error("Face not captured")
                return

            face_emb = encodings[0].tolist()

            voice_emb = None
            if audio_data:
                voice_emb = get_voice_embedding(audio_data.read())

            res = create_student(new_name, face_embedding=face_emb, voice_embedding=voice_emb)

            if res:
                train_classifier()
                st.session_state.student_data = res[0]
                st.success("Profile created!")
                time.sleep(1)
                st.rerun()

    footer_dashboard()