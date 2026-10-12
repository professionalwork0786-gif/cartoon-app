
import streamlit as st
import cv2
import numpy as np
import tempfile
import os
from moviepy.editor import VideoFileClip

# Streamlit Page Setup
st.set_page_config(page_title="AI Professional Cartoonizer", page_icon="🎬", layout="centered")

st.title("🎬 AI Video Cartoonizer & Audio Shift Pro")
st.write("Apni kisi bhi video ko HD Cartoon style me convert karein aur copyright-free audio ke sath download karein.")

# Settings Sidebar for Customization
st.sidebar.header("🎨 Cartoon Settings")
blur_val = st.sidebar.slider("Edge Smoothness", 3, 11, 7, step=2)
edge_ksize = st.sidebar.slider("Line Detail Thickness", 5, 15, 9, step=2)
color_quant = st.sidebar.slider("Color Painting Effect", 2, 8, 4)

st.sidebar.header("🎵 Audio Copyright Settings")
speed_factor = st.sidebar.slider("Audio Speed/Pitch Shift", 0.90, 1.15, 1.05, step=0.01)

uploaded_file = st.file_uploader("Ek Video File Upload Karein (MP4 / MOV / AVI)", type=["mp4", "mov", "avi"])

def cartoonize_frame(frame, blur_v, edge_k, colors):
    # 1. Color Quantization for Painting Look
    data = np.float32(frame).reshape((-1, 3))
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 0.2)
    _, labels, centers = cv2.kmeans(data, colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    centers = np.uint8(centers)
    quantized = centers[labels.flatten()].reshape(frame.shape)

    # 2. Bilateral Filter for Smooth Cartoon Skin/Background
    smoothed = cv2.bilateralFilter(quantized, d=9, sigmaColor=75, sigmaSpace=75)

    # 3. Edge Detection for Sharp Cartoon Outlines
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.medianBlur(gray, blur_v)
    edges = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, edge_k, 2)
    edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

    # 4. Combine Smooth Colors with Edges
    cartoon = cv2.bitwise_and(smoothed, edges_bgr)
    return cartoon

if uploaded_file is not None:
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    tfile.write(uploaded_file.read())
    video_path = tfile.name

    st.video(video_path)

    if st.button("🚀 Process & Convert to Cartoon", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()

        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        output_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        output_path = output_temp.name
        output_temp.close()

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        frame_count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            cartoon_frame = cartoonize_frame(frame, blur_val, edge_ksize, color_quant)
            out.write(cartoon_frame)

            frame_count += 1
            if total_frames > 0:
                progress = int((frame_count / total_frames) * 100)
                progress_bar.progress(progress)
                status_text.text(f"Processing Video Frames: {frame_count}/{total_frames} ({progress}%)")

        cap.release()
        out.release()

        status_text.text("Merging Audio & Fixing Copyright Pitch...")

        try:
            clip = VideoFileClip(video_path)
            cartoon_clip = VideoFileClip(output_path)

            if clip.audio is not None:
                # Modifying Audio speed and pitch slightly to prevent copyright match
                new_audio = clip.audio.fl_time(lambda t: t * speed_factor, keep_duration=False)
                final_clip = cartoon_clip.set_audio(new_audio)
            else:
                final_clip = cartoon_clip

            final_output = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            final_output_path = final_output.name
            final_output.close()

            final_clip.write_videofile(final_output_path, codec='libx264', audio_codec='aac', logger=None)

            st.success("🎉 Video successfully cartoonized!")
            st.video(final_output_path)

            with open(final_output_path, "rb") as file:
                st.download_button("📥 Download Full HD Cartoon Video", file, file_name="cartoon_pro_video.mp4", mime="video/mp4")

        except Exception as e:
            st.error(f"Error processing video audio: {e}")
