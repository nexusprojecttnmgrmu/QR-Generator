# qr_auth_app.py

import streamlit as st
import qrcode
import numpy as np
from PIL import Image
from pyzbar.pyzbar import decode
import io
import datetime
import pandas as pd

# Secret watermark pattern
secret_pattern = [
    [1, 0, 1],
    [0, 1, 0],
    [1, 0, 1]
]

# --- Utility Functions ---
def generate_qr(data):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(data)
    qr.make()
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")

def embed_watermark(img, pattern, start_pos):
    arr = np.array(img)
    for i in range(len(pattern)):
        for j in range(len(pattern[0])):
            y, x = start_pos[1] + i, start_pos[0] + j
            if 0 <= y < arr.shape[0] and 0 <= x < arr.shape[1]:
                arr[y, x] = [0,0,0] if pattern[i][j] == 1 else [255,255,255]
    return Image.fromarray(arr)

def verify_watermark(img, pattern, start_pos):
    arr = np.array(img)
    for i in range(len(pattern)):
        for j in range(len(pattern[0])):
            y, x = start_pos[1] + i, start_pos[0] + j
            if not (0 <= y < arr.shape[0] and 0 <= x < arr.shape[1]):
                return False
            is_black = all(v < 50 for v in arr[y, x])
            if pattern[i][j] != int(is_black):
                return False
    return True

def decode_qr(img):
    decoded = decode(img)
    return decoded[0].data.decode("utf-8") if decoded else "UNREADABLE"

# --- Streamlit App ---
st.set_page_config(page_title="QR Authenticator", layout="wide")
st.title("🧪 QR Code Generator & Verifier for Medicines")

# Initialize log in session state
if "log" not in st.session_state:
    st.session_state.log = []

tabs = st.tabs(["🔐 Generate QR", "🔍 Verify QR", "📜 Scan Log"])

# --- Tab: Generate QR Code ---
with tabs[0]:
    st.subheader("Generate Watermarked QR Code")
    med = st.text_input("Medicine Name", key="gen_med")
    batch = st.text_input("Batch Number", key="gen_batch")

    if st.button("Generate QR Code"):
        if med and batch:
            data_str = f"Medicine: {med}, Batch#: {batch}"
            qr_img = generate_qr(data_str)
            w, h = qr_img.size
            final_img = embed_watermark(qr_img, secret_pattern, (w-10, h-10))
            st.image(final_img, caption="🔳 Watermarked QR", use_container_width=True)

            buf = io.BytesIO()
            final_img.save(buf, format="PNG")
            st.download_button("📥 Download QR Code", buf.getvalue(), "watermarked_qr.png")
        else:
            st.warning("Please enter both Medicine Name and Batch Number.")

# --- Tab: Verify QR Code ---
with tabs[1]:
    st.subheader("Verify QR Code and Check Authenticity")
    uploaded = st.file_uploader("Upload QR Image", type=["png","jpg","jpeg"], key="ver_uploader")
    if uploaded:
        img = Image.open(uploaded).convert("RGB")
        w, h = img.size
        st.image(img, caption="📷 Uploaded QR", use_container_width=True)

        # Decode & verify
        qr_text = decode_qr(img)
        is_auth = verify_watermark(img, secret_pattern, (w-10,h-10))
        status = "✅ AUTHENTIC" if is_auth else "❌ COUNTERFEIT"

        # Show details
        st.markdown("**🔎 Extracted QR Data:**")
        st.code(qr_text)
        st.markdown(f"**🔐 Watermark Match:** {'Matched' if is_auth else 'Not Matched'}")
        st.markdown(f"**📋 Final Status:** {status}")

        # Append to session log
        st.session_state.log.append({
            "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Filename": uploaded.name,
            "QR Data": qr_text,
            "Watermark": "Matched" if is_auth else "Not Matched",
            "Status": status
        })

# --- Tab: Scan Log ---
with tabs[2]:
    st.subheader("📜 Session Scan Log")
    if st.session_state.log:
        df = pd.DataFrame(st.session_state.log)
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Full Log as CSV", csv, "scan_log.csv")
    else:
        st.info("No scans yet this session.")

