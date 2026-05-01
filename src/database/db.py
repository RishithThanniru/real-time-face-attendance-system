import streamlit as st
from src.database.config import supabase
import bcrypt


# =========================
# AUTH FUNCTIONS
# =========================
def hash_pass(pwd):
    return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()


def check_pass(pwd, hashed):
    if not hashed:
        return False
    return bcrypt.checkpw(pwd.encode(), hashed.encode())


# =========================
# TEACHERS
# =========================
def check_teacher_exists(username):
    try:
        res = supabase.table("teachers").select("username").eq("username", username).execute()
        return len(res.data) > 0
    except:
        return False


def create_teacher(username, password, name):
    try:
        data = {
            "username": username,
            "password": hash_pass(password),
            "name": name
        }
        return supabase.table("teachers").insert(data).execute().data
    except Exception as e:
        st.error(f"Create teacher error: {e}")
        return []


def teacher_login(username, password):
    try:
        res = supabase.table("teachers").select("*").eq("username", username).execute()

        if res.data:
            teacher = res.data[0]

            if check_pass(password, teacher.get("password")):
                return teacher   # ✅ MUST return full object (includes id)

        return None

    except Exception as e:
        st.error(f"Login error: {e}")
        return None


# =========================
# STUDENTS
# =========================
def get_all_students():
    try:
        return supabase.table("students").select("*").execute().data or []
    except:
        return []


def create_student(new_name, face_embedding=None, voice_embedding=None):
    try:
        data = {
            "name": new_name,
            "face_embedding": face_embedding,
            "voice_embedding": voice_embedding
        }
        return supabase.table("students").insert(data).execute().data
    except Exception as e:
        st.error(f"Create student error: {e}")
        return []


# =========================
# SUBJECTS
# =========================
def create_subject(subject_code, name, section, teacher_id):
    try:
        if not teacher_id:
            return []  # ✅ prevent UUID error

        data = {
            "subject_code": subject_code,
            "name": name,
            "section": section,
            "teacher_id": teacher_id
        }
        return supabase.table("subjects").insert(data).execute().data
    except Exception as e:
        st.error(f"Create subject error: {e}")
        return []


def get_teacher_subjects(teacher_id):
    try:
        if not teacher_id:
            return []  # ✅ FIX UUID crash

        res = supabase.table("subjects") \
            .select("*") \
            .eq("teacher_id", teacher_id) \
            .execute()

        subjects = res.data or []

        for sub in subjects:
            sid = sub.get("id")

            # total students
            students = supabase.table("subject_students") \
                .select("id") \
                .eq("subject_id", sid) \
                .execute().data or []

            sub["total_students"] = len(students)

            # total classes
            attendance = supabase.table("attendance") \
                .select("timestamp") \
                .eq("subject_id", sid) \
                .execute().data or []

            timestamps = [a.get("timestamp") for a in attendance if a.get("timestamp")]
            sub["total_classes"] = len(set(timestamps))

        return subjects

    except Exception as e:
        st.error(f"Error loading subjects: {e}")
        return []


# =========================
# ENROLLMENT
# =========================
def enroll_student_to_subject(student_id, subject_id):
    try:
        if not student_id or not subject_id:
            return []

        data = {"student_id": student_id, "subject_id": subject_id}
        return supabase.table("subject_students").insert(data).execute().data
    except Exception as e:
        st.error(f"Enroll error: {e}")
        return []


def unenroll_student_to_subject(student_id, subject_id):
    try:
        return supabase.table("subject_students") \
            .delete() \
            .eq("student_id", student_id) \
            .eq("subject_id", subject_id) \
            .execute().data
    except Exception as e:
        st.error(f"Unenroll error: {e}")
        return []


def get_student_subjects(student_id):
    try:
        # ✅ FIX: include subject data (important)
        return supabase.table("subject_students") \
            .select("*, subjects(*)") \
            .eq("student_id", student_id) \
            .execute().data or []
    except Exception as e:
        st.error(f"Error fetching subjects: {e}")
        return []


# =========================
# ATTENDANCE
# =========================
def get_student_attendance(student_id):
    try:
        return supabase.table("attendance") \
            .select("*") \
            .eq("student_id", student_id) \
            .execute().data or []
    except Exception as e:
        st.error(f"Attendance error: {e}")
        return []


def create_attendance(logs):
    try:
        if not logs:
            return []
        return supabase.table("attendance").insert(logs).execute().data
    except Exception as e:
        st.error(f"Insert error: {e}")
        return []


def get_attendance_for_teacher(teacher_id):
    try:
        if not teacher_id:
            return []

        subjects = supabase.table("subjects") \
            .select("id") \
            .eq("teacher_id", teacher_id) \
            .execute().data or []

        subject_ids = [s.get("id") for s in subjects if s.get("id")]

        if not subject_ids:
            return []

        return supabase.table("attendance") \
            .select("*") \
            .in_("subject_id", subject_ids) \
            .execute().data or []

    except Exception as e:
        st.error(f"Teacher attendance error: {e}")
        return []