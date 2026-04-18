import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image
from streamlit_drawable_canvas import st_canvas
from pathlib import Path
import datetime
import sqlite3
import random
import zipfile
import io
import os 

REAL_IMAGE_DIR = Path("./images/REAL")
AI_IMAGE_DIR = Path("./images/AI")
MASK_DIR = Path("masks")
RESULTS_FILE = "results.csv"

MASK_DIR.mkdir(exist_ok=True)

st.set_page_config(layout="wide")


def zip_png_folder(folder_path):
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(".png"):
                filepath = os.path.join(folder_path, filename)
                zip_file.write(filepath, arcname=filename)

    zip_buffer.seek(0)
    return zip_buffer


def show_admin_login():
    admin_password = st.text_input("Admin password", type="password")

    if st.button("Enter"):
        if admin_password == st.secrets["ADMIN_PASSWORD"]:
            st.session_state.is_admin = True
            st.toast("Admin access granted ✅")
            st.rerun()
        else:
            st.error("Wrong password ❌")
    if st.button("Exit"):
        st.session_state.is_admin = False
        st.session_state.show_admin_login = False
        st.rerun()


def show_admin_stuff():
    with open(RESULTS_FILE, "rb") as f:
        st.download_button(
            label="Download log",
            data=f,
            file_name="log.csv",
            mime="text/csv"
        )
        
    zip_data = zip_png_folder("./masks")

    st.download_button(
        label="Download PNGs as ZIP",
        data=zip_data,
        file_name="masks.zip",
        mime="application/zip"
    )

    if st.button("Exit"):
        st.session_state.is_admin = False
        st.session_state.show_admin_login = False
        st.rerun()




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

def explain_what_to_do_to_the_user():
    st.markdown("""## Instructions

In this experiment, you will be shown a series of images. Each image is **either AI‑generated or a REAL photo**.

Your task is to **classify** each image.  
Before making your choice, we ask you to **highlight the areas of the image** that were most important for your decision.

For example:
- If you notice **imperfections** that you think come from AI generation, color them.
- If you see **details that you believe an AI model could not generate**, color those as well.

After **10 images**, you will be shown how an **AI model performs the same task**, including which parts of the images it focuses on.  
This should help you better understand how to distinguish **AI‑generated images** from **real photos**.

After that, you will be asked to try again with **another set of 10 images**.""")
    if st.button("OK"):
        st.session_state.intro = True
        st.rerun()

def interpretability_explenaticon():
    if st.session_state.what_explenation == 0:
        st.text("TODO for SHAP")
    elif st.session_state.what_explenation == 1:
        st.text("TODO for GRADCAM")
    elif st.session_state.what_explenation == 2:
        st.text("TODO for counterfactuals")
        #TODO show the images of the correct method, and let the user of back and forth trough them as much as they want (or put all of them in the page one above the other)
    if st.button("OK"):
        st.session_state.interpretability_explenation = True
        st.rerun()

col_left, col_spacer = st.columns([1, 20])

with col_left:
    if st.button("🔒", help="Admin access"):
        st.session_state.show_admin_login = True

if "show_admin_login" not in st.session_state:
    st.session_state.show_admin_login = False

if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

if "idx" not in st.session_state:
    real_image_paths = sorted(REAL_IMAGE_DIR.glob("*.png")) + sorted(REAL_IMAGE_DIR.glob("*.jpg")) + sorted(REAL_IMAGE_DIR.glob("*.JPEG")) 
    real_image_paths_with_label = [(s, "REAL") for s in real_image_paths]
    ai_image_paths = sorted(AI_IMAGE_DIR.glob("*.png")) + sorted(AI_IMAGE_DIR.glob("*.jpg")) + sorted(AI_IMAGE_DIR.glob("*.JPEG")) 
    ai_image_paths_with_label = [(s, "AI") for s in ai_image_paths]

    st.session_state.real_images_n = len(real_image_paths_with_label)
    st.session_state.all_image_paths = (real_image_paths_with_label + ai_image_paths_with_label)
    st.session_state.all_image_len = len(st.session_state.all_image_paths)
    random.shuffle(st.session_state.all_image_paths)
    init_db()
    random_number = random.randint(0, len(st.session_state.all_image_paths)-1)
    st.session_state.idx = random_number
    user_id = create_user_and_get_id()
    st.session_state.user_id = user_id 
    st.session_state.starting_index = st.session_state.idx - 1
    st.session_state.no_explenation_left = 10
    st.session_state.with_explenation_left = 10
    st.session_state.interpretability_explenation = False
    st.session_state.what_explenation = random.randint(0, 2)


if st.session_state.show_admin_login and not st.session_state.is_admin:
    show_admin_login()
elif st.session_state.is_admin:
    show_admin_stuff()
elif "intro" not in st.session_state:
    st.session_state.intro = False
    explain_what_to_do_to_the_user()
elif st.session_state.no_explenation_left == 0 and not st.session_state.interpretability_explenation:
    interpretability_explenaticon()
else:
    if st.session_state.with_explenation_left <= 0:
        st.title("✅ Annotation complete")
        st.stop()

    image_path = st.session_state.all_image_paths[st.session_state.idx % st.session_state.all_image_len][0]
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

        if not st.session_state.interpretability_explenation:
            iterpretability_method = "None"
        elif st.session_state.what_explenation == 0:
            iterpretability_method = "SHAP"
        elif st.session_state.what_explenation == 1:
            iterpretability_method = "GRADCAM"
        elif st.session_state.what_explenation == 2:
            iterpretability_method = "Counterfactuals"
        else:
            iterpretability_method = "ERROR"
        
        entry = {
            "user_id": st.session_state.user_id,
            "image_id": image_path.name,
            "iterpretability_method": iterpretability_method,
            "user_label": user_label,
            "true_label": st.session_state.all_image_paths[st.session_state.idx % st.session_state.all_image_len][1],
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

        if st.session_state.interpretability_explenation:
            st.session_state.with_explenation_left -= 1
        else:
            st.session_state.no_explenation_left -= 1
        st.session_state.idx += 1
        st.rerun()