import streamlit as st
import google.generativeai as genai
import subprocess
import speech_recognition as sr
import tempfile
import os

# Configure Google Generative AI API key (make sure the API key is added to the secrets)
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Streamlit UI setup
st.title("Cloud-Based Video Editor with AI Features")

# Video Upload
video_file = st.file_uploader("Upload a Video", type=["mp4", "avi", "mov"])

if video_file is not None:
    # Display the uploaded video
    st.video(video_file)

    # Temporary path to save the uploaded video
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
        tmp_video.write(video_file.read())
        tmp_video_path = tmp_video.name

    # **Video Duration (using ffmpeg)**
    result = subprocess.run(
        ["ffmpeg", "-i", tmp_video_path], 
        stderr=subprocess.PIPE, stdout=subprocess.PIPE
    )
    duration = None
    for line in result.stderr.decode().splitlines():
        if "Duration" in line:
            duration = line.split(",")[0].split(" ")[1]
            break
    if duration:
        st.write(f"Video Duration: {duration}")

    # **Trim Video**
    st.subheader("Trim Video")
    start_time = st.number_input("Start Time (in seconds)", min_value=0, max_value=int(duration.split(":")[2]), step=1)
    end_time = st.number_input("End Time (in seconds)", min_value=start_time, max_value=int(duration.split(":")[2]), step=1)

    if st.button("Trim Video"):
        trimmed_video_path = "trimmed_video.mp4"
        subprocess.run(
            ["ffmpeg", "-i", tmp_video_path, "-ss", str(start_time), "-to", str(end_time), "-c", "copy", trimmed_video_path]
        )
        st.video(trimmed_video_path)

    # **Merge Videos**
    st.subheader("Merge Videos")
    second_video_file = st.file_uploader("Upload a second video to merge", type=["mp4", "avi", "mov"])
    if second_video_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_second_video:
            tmp_second_video.write(second_video_file.read())
            second_video_path = tmp_second_video.name

        if st.button("Merge Videos"):
            merged_video_path = "merged_video.mp4"
            subprocess.run(
                ["ffmpeg", "-i", tmp_video_path, "-i", second_video_path, "-c", "copy", "-y", merged_video_path]
            )
            st.video(merged_video_path)

    # **Extract Audio from Video**
    st.subheader("Extract Audio from Video")
    if st.button("Extract Audio"):
        audio_file_path = "extracted_audio.mp3"
        subprocess.run(
            ["ffmpeg", "-i", tmp_video_path, "-q:a", "0", "-map", "a", audio_file_path]
        )
        st.audio(audio_file_path)
        st.write(f"Audio saved as {audio_file_path}")

    # **Generate Transcription**
    def extract_audio_and_transcribe(video_file):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            audio_file_path = temp_audio.name
            subprocess.run(
                ["ffmpeg", "-i", video_file, audio_file_path]
            )

            recognizer = sr.Recognizer()
            with sr.AudioFile(audio_file_path) as audio_source:
                audio_data = recognizer.record(audio_source)
            transcript = recognizer.recognize_google(audio_data)

            # Clean up temporary audio file
            os.remove(audio_file_path)

            return transcript

    def generate_transcription(video_file):
        try:
            transcript = extract_audio_and_transcribe(video_file)
            st.subheader("Generated Transcription")
            st.text_area("Transcription", transcript, height=200)
            # Option to download transcription as a text file
            with open("transcription.txt", "w") as f:
                f.write(transcript)
            st.download_button("Download Transcription", "transcription.txt")
        except Exception as e:
            st.error(f"Error generating transcription: {e}")

    if st.button("Generate Transcription"):
        if video_file is not None:
            generate_transcription(tmp_video_path)
        else:
            st.warning("Please upload a video to generate transcription.")

    # **Apply Filters and Effects**
    st.subheader("Apply Filters and Effects")
    if st.button("Apply Brightness Effect"):
        # Applying a brightness effect (using ffmpeg)
        brightness_video_path = "brightness_video.mp4"
        subprocess.run(
            ["ffmpeg", "-i", tmp_video_path, "-vf", "eq=brightness=0.2", brightness_video_path]
        )
        st.video(brightness_video_path)

    # **Add Background Music**
    st.subheader("Add Background Music to Video")
    background_music = st.file_uploader("Upload Background Music (MP3)", type=["mp3"])
    if background_music is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_music:
            temp_music.write(background_music.read())
            audio_file_path = temp_music.name

        if st.button("Add Background Music"):
            final_video_with_music_path = "video_with_music.mp4"
            subprocess.run(
                ["ffmpeg", "-i", tmp_video_path, "-i", audio_file_path, "-c:v", "copy", "-c:a", "aac", "-strict", "experimental", final_video_with_music_path]
            )
            st.video(final_video_with_music_path)

    # **AI Summarization**
    st.subheader("AI Generated Summary (using Google Generative AI)")
    prompt = st.text_input("Enter your prompt:", "Summarize the video content.")
    if st.button("Generate AI Summary"):
        try:
            transcript = extract_audio_and_transcribe(tmp_video_path)
            model = genai.GenerativeModel('gemini-1.5-flash')
            summary_response = model.generate_content(transcript)
            st.write("AI Generated Summary:")
            st.write(summary_response.text)
        except Exception as e:
            st.error(f"Error generating AI summary: {e}")

    # Clean up temporary files
    def clean_up_files():
        files_to_remove = [
            "trimmed_video.mp4",
            "merged_video.mp4",
            "video_with_effect.mp4",
            "video_with_music.mp4",
            "transcription.txt"
        ]
        for file in files_to_remove:
            if os.path.exists(file):
                os.remove(file)

    # Auto-clean files (optional)
    if st.button("Clean Up Files"):
        clean_up_files()
        st.write("Temporary files cleaned up.")
