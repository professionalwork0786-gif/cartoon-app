import streamlit as st
import cv2
import numpy as np
import tempfile
import os

st.set_page_config(page_title="Fast AI Cartoonizer", page_icon="🎬", layout="centered")

st.title("🎬 Fast Video Cartoonizer")
st.write("Apni video upload karein aur turant clean cartoon video download karein!")

uploaded_file = st.file_uploader("Ek Video File Chunein (MP4/MOV)", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    tfile.write(uploaded_file.read())
    video_path = tfile.name

    st.video(video_path)

    if st.button("🚀 Convert to Cartoon", type="primary"):
        with st.spinner("Video process ho rahi hai, kripya intezar karein..."):
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            output_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            output_path = output_temp.name
            output_temp.close()

            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                # Fast and clean cartoon filter
                small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
                color = cv2.bilateralFilter(small, d=9, sigmaColor=75, sigmaSpace=75)
                color = cv2.resize(color, (width, height))

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                blur = cv2.medianBlur(gray, 7)
                edges = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 2)
                edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

                cartoon = cv2.bitwise_and(color, edges_bgr)
                out.write(cartoon)

            cap.release()
            out.release()

            st.success("🎉 Video successfully cartoonize ho gayi hai!")
            st.video(output_path)

            with open(output_path, "rb") as file:
                st.download_button("📥 Download Cartoon Video", file, file_name="cartoon_video.mp4", mime="video/mp4")
