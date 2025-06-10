# qr_auth_app.py

import streamlit as st
import qrcode
import numpy as np
from PIL import Image
import io

# Secret watermark pattern
secret_pattern = [
    [1, 0, 1],
    [0, 1, 0],
    [1, 0, 1]
]

# Functions
def generate_qr(data):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(data)
    qr.make()
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    return img

def embed_watermark(img, pattern, start_pos):
    arr = np.array(img)
    for i in range(len(pattern)):
        for j in range(len(pattern[0])):
            y = start_pos[1] + i
            x = start_pos[0] + j
            if y < arr.shape[0] and x < arr.shape[1]:
                arr[y, x] = [0, 0, 0] if pattern[i][j] == 1 else [255, 255, 255]
    return Image.fromarray(arr)

def verify_watermark(img, pattern, start_pos):
    arr = np.array(img)
    for i in range(len(pattern)):
        for j in range(len(pattern[0])):
            y = start_pos[1] + i
            x = start_pos[0] + j
            if y < arr.shape[0] and x < arr.shape[1]:
                pixel = arr[y, x]
                is_black = all(v < 50 for v in pixel)
                if pattern[i][j] != int(is_black):
                    return False
            else:
                return False
    return True

# Streamlit UI
st.set_page_config(page_title="QR Code Authenticator", layout="centered")
st.title("🧪 QR Code Generator & Verifier for Medicines")

tabs = st.tabs(["🔐 Generate QR", "🔍 Verify QR"])

# Tab 1: Generate
with tabs[0]:
    st.subheader("Generate Watermarked QR Code")

    medicine_name = st.text_input("Medicine Name")
    batch_number = st.text_input("Batch Number")

    if st.button("Generate QR Code"):
        if medicine_name and batch_number:
            data = f"Medicine: {medicine_name}, Batch#: {batch_number}"
            qr_img = generate_qr(data)
            width, height = qr_img.size
            start_pos = (width - 10, height - 10)
            final_img = embed_watermark(qr_img, secret_pattern, start_pos)

            st.image(final_img, caption="Watermarked QR Code", use_container_width=True)
            
            # Save image as download
            buf = io.BytesIO()
            final_img.save(buf, format="PNG")
            st.download_button("📥 Download QR", data=buf.getvalue(), file_name="watermarked_qr.png")
        else:
            st.warning("Please enter both medicine name and batch number.")

# Tab 2: Verify
with tabs[1]:
    st.subheader("Verify Uploaded QR Code")

    uploaded_file = st.file_uploader("Upload a QR Code Image", type=["png", "jpg", "jpeg"])

    if uploaded_file:
        img = Image.open(uploaded_file).convert("RGB")
        width, height = img.size
        start_pos = (width - 10, height - 10)
        result = verify_watermark(img, secret_pattern, start_pos)

        st.image(img, caption="Uploaded QR Code", use_container_width=True)

        if result:
            st.success("✅ QR Code is AUTHENTIC. Watermark matched.")
        else:
            st.error("❌ QR Code is FAKE or TAMPERED. Watermark mismatch.")
