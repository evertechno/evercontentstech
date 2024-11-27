import streamlit as st
import google.generativeai as genai
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip
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

    # Load video for editing
    video_clip = VideoFileClip(video_file)
    duration = video_clip.duration
    st.write(f"Video Duration: {duration:.2f} seconds")

    # **Trim Video**
    st.subheader("Trim Video")
    start_time = st.number_input("Start Time (in seconds)", min_value=0, max_value=duration, step=1)
    end_time = st.number_input("End Time (in seconds)", min_value=start_time, max_value=duration, step=1)

    if st.button("Trim Video"):
        trimmed_clip = video_clip.subclip(start_time, end_time)
        trimmed_clip.write_videofile("trimmed_video.mp4", codec="libx264")
        st.video("trimmed_video.mp4")

    # **Merge Videos**
    st.subheader("Merge Videos")
    second_video_file = st.file_uploader("Upload a second video to merge", type=["mp4", "avi", "mov"])
    if second_video_file is not None:
        second_clip = VideoFileClip(second_video_file)
        if st.button("Merge Videos"):
            final_clip = concatenate_videoclips([video_clip, second_clip])
            final_clip.write_videofile("merged_video.mp4", codec="libx264")
            st.video("merged_video.mp4")

    # **Extract Audio from Video**
    st.subheader("Extract Audio from Video")
    if st.button("Extract Audio"):
        audio_clip = video_clip.audio
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        audio_clip.write_audiofile(temp_audio.name)
        st.audio(temp_audio.name)
        st.write(f"Audio saved as {temp_audio.name}")

    # **Generate Transcription**
    def extract_audio_and_transcribe(video_file):
        video_clip = VideoFileClip(video_file)
        audio_clip = video_clip.audio
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        audio_clip.write_audiofile(temp_audio.name)

        recognizer = sr.Recognizer()
        with sr.AudioFile(temp_audio.name) as audio_source:
            audio_data = recognizer.record(audio_source)
        transcript = recognizer.recognize_google(audio_data)
        
        # Clean up temporary audio file
        os.remove(temp_audio.name)
        
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
            generate_transcription(video_file)
        else:
            st.warning("Please upload a video to generate transcription.")

    # **Apply Filters and Effects**
    st.subheader("Apply Filters and Effects")
    if st.button("Apply Brightness Effect"):
        # Applying a simple color effect (adjust brightness)
        from moviepy.editor import vfx
        video_with_effect = video_clip.fx(vfx.colorx, 1.5)  # Increase brightness
        video_with_effect.write_videofile("video_with_effect.mp4", codec="libx264")
        st.video("video_with_effect.mp4")

    # **Add Background Music**
    st.subheader("Add Background Music to Video")
    background_music = st.file_uploader("Upload Background Music (MP3)", type=["mp3"])
    if background_music is not None:
        audio_clip = AudioFileClip(background_music)
        if st.button("Add Background Music"):
            final_video_with_music = video_clip.set_audio(audio_clip)
            final_video_with_music.write_videofile("video_with_music.mp4", codec="libx264")
            st.video("video_with_music.mp4")

    # **AI Summarization**
    st.subheader("AI Generated Summary (using Google Generative AI)")
    prompt = st.text_input("Enter your prompt:", "Summarize the video content.")
    if st.button("Generate AI Summary"):
        try:
            transcript = extract_audio_and_transcribe(video_file)
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
