import streamlit as st
from src.database.config import supabase
import bcrypt


# =========================
# AUTH FUNCTIONS
# =========================
def hash_pass(pwd):
    return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()


def check_pass(pwd, hashed):
    return bcrypt.checkpw(pwd.encode(), hashed.encode())


# =========================
# TEACHERS
# =========================
def check_teacher_exists(username):
    response = supabase.table("teachers").select("username").eq("username", username).execute()
    return len(response.data) > 0


def create_teacher(username, password, name):
    data = {
        "username": username,
        "password": hash_pass(password),
        "name": name
    }
    return supabase.table("teachers").insert(data).execute().data


def teacher_login(username, password):
    response = supabase.table("teachers").select("*").eq("username", username).execute()
    if response.data:
        teacher = response.data[0]
        if check_pass(password, teacher["password"]):
            return teacher
    return None


# =========================
# STUDENTS
# =========================
def get_all_students():
    return supabase.table("students").select("*").execute().data


def create_student(new_name, face_embedding=None, voice_embedding=None):
    data = {
        "name": new_name,
        "face_embedding": face_embedding,
        "voice_embedding": voice_embedding
    }
    return supabase.table("students").insert(data).execute().data


# =========================
# SUBJECTS
# =========================
def create_subject(subject_code, name, section, teacher_id):
    data = {
        "subject_code": subject_code,
        "name": name,
        "section": section,
        "teacher_id": teacher_id
    }
    return supabase.table("subjects").insert(data).execute().data


def get_teacher_subjects(teacher_id):
    try:
        response = supabase.table("subjects") \
            .select("*") \
            .eq("teacher_id", teacher_id) \
            .execute()

        subjects = response.data

        for sub in subjects:
            sub["total_students"] = len(
                supabase.table("subject_students")
                .select("*")
                .eq("subject_id", sub["id"])
                .execute().data
            )

            attendance = supabase.table("attendance") \
                .select("timestamp") \
                .eq("subject_id", sub["id"]) \
                .execute().data

            sub["total_classes"] = len(set(log["timestamp"] for log in attendance))

        return subjects

    except Exception as e:
        st.error(f"Error loading subjects: {e}")
        return []


# =========================
# ENROLLMENT
# =========================
def enroll_student_to_subject(student_id, subject_id):
    data = {"student_id": student_id, "subject_id": subject_id}
    return supabase.table("subject_students").insert(data).execute().data


def unenroll_student_to_subject(student_id, subject_id):
    return supabase.table("subject_students") \
        .delete() \
        .eq("student_id", student_id) \
        .eq("subject_id", subject_id) \
        .execute().data


def get_student_subjects(student_id):
    try:
        return supabase.table("subject_students") \
            .select("*") \
            .eq("student_id", student_id) \
            .execute().data
    except Exception as e:
        st.error(f"Error fetching subjects: {e}")
        return []


# =========================
# ATTENDANCE (FIXED)
# =========================
def get_student_attendance(student_id):
    try:
        response = supabase.table("attendance") \
            .select("*") \
            .eq("student_id", student_id) \
            .execute()

        return response.data

    except Exception as e:
        st.error(f"Attendance error: {e}")
        return []


def create_attendance(logs):
    try:
        return supabase.table("attendance").insert(logs).execute().data
    except Exception as e:
        st.error(f"Insert error: {e}")
        return []


def get_attendance_for_teacher(teacher_id):
    try:
        subjects = supabase.table("subjects") \
            .select("id") \
            .eq("teacher_id", teacher_id) \
            .execute().data

        subject_ids = [s["id"] for s in subjects]

        if not subject_ids:
            return []

        return supabase.table("attendance") \
            .select("*") \
            .in_("subject_id", subject_ids) \
            .execute().data

    except Exception as e:
        st.error(f"Teacher attendance error: {e}")
        return []