import dlib
import numpy as np
import face_recognition_models
from sklearn.svm import SVC
import streamlit as st

from src.database.db import get_all_students


# =========================
# LOAD MODELS (CACHED)
# =========================
@st.cache_resource
def load_dlib_models():
    detector = dlib.get_frontal_face_detector()

    sp = dlib.shape_predictor(
        face_recognition_models.pose_predictor_model_location()
    )

    facerec = dlib.face_recognition_model_v1(
        face_recognition_models.face_recognition_model_location()
    )

    return detector, sp, facerec


# =========================
# GET FACE EMBEDDINGS
# =========================
def get_face_embeddings(image_np):
    detector, sp, facerec = load_dlib_models()
    faces = detector(image_np, 1)

    encodings = []

    for face in faces:
        shape = sp(image_np, face)
        face_descriptor = facerec.compute_face_descriptor(image_np, shape, 1)
        encodings.append(np.array(face_descriptor))

    return encodings


# =========================
# TRAIN MODEL
# =========================
@st.cache_resource
def get_trained_model():
    X = []
    y = []

    student_db = get_all_students()

    # ❌ No students in DB
    if not student_db:
        return None

    for student in student_db:
        embedding = student.get("face_embedding")
        student_id = student.get("student_id")

        if embedding and student_id:
            X.append(np.array(embedding))
            y.append(student_id)

    # ❌ No valid embeddings
    if len(X) == 0:
        return None

    clf = SVC(kernel="linear", probability=True, class_weight="balanced")

    try:
        clf.fit(X, y)
    except ValueError:
        return None

    return {"clf": clf, "X": X, "y": y}


# =========================
# RE-TRAIN TRIGGER
# =========================
def train_classifier():
    st.cache_resource.clear()
    model_data = get_trained_model()
    return bool(model_data)


# =========================
# PREDICT ATTENDANCE
# =========================
def predict_attendance(class_image_np):
    encodings = get_face_embeddings(class_image_np)

    detected_students = {}

    model_data = get_trained_model()

    # ❌ No model / no DB data
    if not model_data:
        return detected_students, [], len(encodings)

    clf = model_data["clf"]
    X_train = model_data["X"]
    y_train = model_data["y"]

    all_students = sorted(list(set(y_train)))

    # ❌ No students at all
    if len(all_students) == 0:
        return detected_students, [], len(encodings)

    for encoding in encodings:
        try:
            # ✅ Case: multiple students
            if len(all_students) >= 2:
                predicted_id = int(clf.predict([encoding])[0])

            # ✅ Case: only one student
            else:
                predicted_id = int(all_students[0])

        except Exception:
            continue  # skip if prediction fails

        # ✅ Get reference embedding safely
        if predicted_id in y_train:
            idx = y_train.index(predicted_id)
            student_embedding = X_train[idx]
        else:
            continue

        # ✅ Distance calculation
        best_match_score = np.linalg.norm(student_embedding - encoding)

        resemblance_threshold = 0.6

        # ✅ Final match check
        if best_match_score <= resemblance_threshold:
            detected_students[predicted_id] = True

    return detected_students, all_students, len(encodings)