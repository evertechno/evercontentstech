import streamlit as st
import moviepy.video.io.ffmpeg_tools as ffmpeg_tools
from moviepy.editor import AudioFileClip
import tempfile
import os
import speech_recognition as sr
from moviepy.video.io.VideoFileClip import VideoFileClip  # Directly using VideoFileClip instead of moviepy.editor

# Streamlit UI setup
st.title("Cloud-Based Video Editor with AI Features")

# Video Upload
video_file = st.file_uploader("Upload a Video", type=["mp4", "avi", "mov"])

if video_file is not None:
    # Display the uploaded video
    st.video(video_file)

    # Save the video temporarily
    temp_video_path = tempfile.mktemp(suffix=".mp4")
    with open(temp_video_path, "wb") as f:
        f.write(video_file.read())

    # **Trim Video**
    st.subheader("Trim Video")
    video_clip = VideoFileClip(temp_video_path)
    duration = video_clip.duration

    # Ensure consistency of types by casting start_time and end_time to float
    start_time = st.number_input("Start Time (in seconds)", min_value=0.0, max_value=duration, step=0.1)
    end_time = st.number_input("End Time (in seconds)", min_value=start_time, max_value=duration, step=0.1)

    if st.button("Trim Video"):
        ffmpeg_tools.ffmpeg_extract_subclip(temp_video_path, start_time, end_time, targetname="trimmed_video.mp4")
        st.video("trimmed_video.mp4")

    # **Merge Videos**
    st.subheader("Merge Videos")
    second_video_file = st.file_uploader("Upload a second video to merge", type=["mp4", "avi", "mov"])
    if second_video_file is not None:
        # Save second video temporarily
        temp_second_video_path = tempfile.mktemp(suffix=".mp4")
        with open(temp_second_video_path, "wb") as f:
            f.write(second_video_file.read())
        
        if st.button("Merge Videos"):
            merged_video_path = "merged_video.mp4"
            ffmpeg_tools.ffmpeg_concat_videos([temp_video_path, temp_second_video_path], merged_video_path)
            st.video(merged_video_path)

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
            with open("transcription.txt", "w") as f:
                f.write(transcript)
            st.download_button("Download Transcription", "transcription.txt")
        except Exception as e:
            st.error(f"Error generating transcription: {e}")

    if st.button("Generate Transcription"):
        if video_file is not None:
            generate_transcription(temp_video_path)
        else:
            st.warning("Please upload a video to generate transcription.")

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
