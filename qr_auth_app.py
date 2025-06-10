# qr_auth_app.py

import streamlit as st
import qrcode
import numpy as np
from PIL import Image
import cv2
import io
import base64
import pandas as pd
from datetime import datetime

# Secret watermark pattern (3x3 binary matrix)
secret_pattern = [
    [1, 0, 1],
    [0, 1, 0],
    [1, 0, 1]
]

def embed_watermark(img, pattern, start_pos):
    arr = np.array(img.convert("RGB"))
    for i in range(len(pattern)):
        for j in range(len(pattern[0])):
            y = start_pos[1] + i
            x = start_pos[0] + j
            if y < arr.shape[0] and x < arr.shape[1]:
                arr[y, x] = [0, 0, 0] if pattern[i][j] == 1 else [255, 255, 255]
    return Image.fromarray(arr)

def verify_watermark(img, pattern, start_pos):
    arr = np.array(img.convert("RGB"))
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

def decode_qr_opencv(image: Image.Image):
    cv_image = np.array(image.convert('RGB'))
    cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)
    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(cv_image)
    return data if data else "Unreadable"

st.title("🔐 QR Code Authenticator for Medicines")
option = st.radio("Choose an action:", ["Generate QR", "Verify QR (Single)", "Verify QR (Batch Upload)"])

# ----------------------------------------
# QR Code Generation
# ----------------------------------------
if option == "Generate QR":
    st.subheader("🧪 QR Code Generator with Watermark")
    medicine_name = st.text_input("Enter Medicine Name:")
    batch_number = st.text_input("Enter Batch Number:")
    
    if st.button("Generate QR Code"):
        if medicine_name and batch_number:
            qr_data = f"Medicine: {medicine_name}, Batch#: {batch_number}"
            qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
            qr.add_data(qr_data)
            qr.make()
            img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
            start_pos = (img.size[0] - 10, img.size[1] - 10)
            watermarked_img = embed_watermark(img, secret_pattern, start_pos)
            
            st.image(watermarked_img, caption="NEXUS AUTH QR Code", use_container_width=True)
            
            buffered = io.BytesIO()
            watermarked_img.save(buffered, format="PNG")
            b64 = base64.b64encode(buffered.getvalue()).decode()
            href = f'<a href="data:file/png;base64,{b64}" download="NEXUSAUTH_qr.png">📥 Download QR Code</a>'
            st.markdown(href, unsafe_allow_html=True)
        else:
            st.warning("Please enter both medicine name and batch number.")

# ----------------------------------------
# QR Code Verification - Single File
# ----------------------------------------
elif option == "Verify QR (Single)":
    st.subheader("🔍 Verify Uploaded QR Code")
    uploaded_file = st.file_uploader("Upload a QR Code Image", type=["png", "jpg", "jpeg"])
    
    if uploaded_file:
        img = Image.open(uploaded_file).convert("RGB")
        st.image(img, caption="Uploaded QR Code", use_container_width=True)

        qr_text = decode_qr_opencv(img)
        start_pos = (img.size[0] - 10, img.size[1] - 10)
        result = verify_watermark(img, secret_pattern, start_pos)

        st.write("📄 **QR Code Details:**")
        st.code(qr_text)

        if result:
            st.success("✅ This QR Code is AUTHENTIC (Cryptokey matched).")
        else:
            st.error("❌ This QR Code is FAKE or TAMPERED (Cryptokey mismatch).")

# ----------------------------------------
# QR Code Verification - Batch Upload
# ----------------------------------------
elif option == "Verify QR (Batch Upload)":
    st.subheader("🧾 Batch Verification of QR Codes")
    uploaded_files = st.file_uploader("Upload multiple QR Code images", accept_multiple_files=True, type=["png", "jpg", "jpeg"])

    if uploaded_files:
        results = []
        for file in uploaded_files:
            try:
                img = Image.open(file).convert("RGB")
                qr_text = decode_qr_opencv(img)
                start_pos = (img.size[0] - 10, img.size[1] - 10)
                result = verify_watermark(img, secret_pattern, start_pos)
                authenticity = "✅ AUTHENTIC" if result else "❌ COUNTERFEIT"

                results.append({
                    "File Name": file.name,
                    "QR Data": qr_text,
                    "Cryptokey Match": "Yes" if result else "No",
                    "Verification Result": authenticity
                })

            except Exception as e:
                results.append({
                    "File Name": file.name,
                    "QR Data": "Unreadable",
                    "Cryptokey Match": "Error",
                    "Verification Result": f"Error: {str(e)}"
                })

        df = pd.DataFrame(results)
        st.dataframe(df)

        csv = df.to_csv(index=False).encode()
        st.download_button(
            label="📥 Download Verification Report",
            data=csv,
            file_name=f"qr_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime='text/csv',
        )
