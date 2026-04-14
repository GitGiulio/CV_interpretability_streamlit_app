import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image
from streamlit_drawable_canvas import st_canvas
from pathlib import Path
import datetime
import sqlite3
import random

REAL_IMAGE_DIR = Path("images/REAL")
AI_IMAGE_DIR = Path("images/AI")
MASK_DIR = Path("masks")
RESULTS_FILE = "results.csv"

MASK_DIR.mkdir(exist_ok=True)

def init_db(db_path="users.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def create_user_and_get_id(db_path="users.db") -> int:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO users DEFAULT VALUES")
    user_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return user_id




if "idx" not in st.session_state:
    real_image_paths = sorted(REAL_IMAGE_DIR.glob("*.png")) + sorted(REAL_IMAGE_DIR.glob("*.jpg")) 
    real_image_paths_with_label = [(s, "REAL") for s in real_image_paths]
    ai_image_paths = sorted(AI_IMAGE_DIR.glob("*.png")) + sorted(AI_IMAGE_DIR.glob("*.jpg")) 
    ai_image_paths_with_label = [(s, "AI") for s in ai_image_paths]

    st.session_state.real_images_n = len(real_image_paths_with_label)
    st.session_state.all_image_paths = (real_image_paths_with_label + ai_image_paths_with_label)
    random.shuffle(st.session_state.all_image_paths)
    init_db()
    random_number = random.randint(0, len(st.session_state.all_image_paths)-1)
    st.session_state.idx = random_number
    user_id = create_user_and_get_id()
    st.session_state.user_id = user_id 
    st.session_state.starting_index = st.session_state.idx - 1

if st.session_state.idx == st.session_state.starting_index:
    st.title("✅ Annotation complete")
    st.stop()

image_path = st.session_state.all_image_paths[st.session_state.idx][0]
image = Image.open(image_path).convert("RGB")
width, height = image.size

st.title("Human Interpretability Study – Real vs AI Images")
st.write(f"Image {st.session_state.idx - st.session_state.starting_index} / {len(st.session_state.all_image_paths)}")

st.subheader("1️⃣ Highlight regions important for your decision")

canvas = st_canvas(
    fill_color="rgba(255, 0, 0, 0.3)",
    stroke_width=32,
    stroke_color="rgba(255, 0, 0, 0.3)",
    background_image=image,
    width=width,
    height=height,
    drawing_mode="freedraw",
    key=f"canvas_{st.session_state.idx}",
)

st.subheader("2️⃣ Your classification")

user_label = st.radio(
    "This image is:",
    ["REAL", "AI"],
    horizontal=True
)

if st.button("Save & Next"):
    if canvas.image_data is None:
        st.warning("Please mark at least one region.")
        st.stop()

    rgba = canvas.image_data
    alpha = rgba[:, :, 3]
    mask = (alpha > 0).astype(np.uint8) * 255

    mask_path = MASK_DIR / f"user{st.session_state.user_id}_{image_path.stem}_mask.png"
    Image.fromarray(mask).save(mask_path)

    entry = {
        "user_id": st.session_state.user_id,
        "image_id": image_path.name,
        "user_label": user_label,
        "true_label": st.session_state.all_image_paths[st.session_state.idx][1],
        "mask_path": str(mask_path),
        "timestamp": datetime.datetime.now().isoformat(),
        "width": width,
        "height": height,
    }

    df_entry = pd.DataFrame([entry])
    if Path(RESULTS_FILE).exists():
        df_entry.to_csv(RESULTS_FILE, mode="a", header=False, index=False)
    else:
        df_entry.to_csv(RESULTS_FILE, index=False)

    st.session_state.idx += 1
    st.rerun()