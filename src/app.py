import streamlit as st
import sounddevice as sd
import scipy.io.wavfile as wav
from helper import *

st.set_page_config(layout="centered")
st.title("Legal Document Assistant(LDA)")

uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

def record_audio(filename, duration=5, samplerate=44100):
    try:
        st.write("Recording...")
        recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=2, dtype='int16')
        sd.wait()  # Wait until the recording is finished
        wav.write(filename, samplerate, recording)  # Save as WAV file
        st.write("Recording finished.")
        return True
    except Exception as e:
        st.error(f"An error occurred during recording: {e}")
        return False

if uploaded_file is not None:
    document_text = extract_text_from_pdf(uploaded_file)

    tabs = st.tabs(["Document Summary", "Previous Similar Judgments" ])
    # tabs = st.tabs(["Document Summary", "Previous Similar Judgments ","What Happened Next"])

    with tabs[0]:  # Document Summary tab
        if "summary_text" not in st.session_state:
            st.session_state.summary_text = st.write_stream(get_summary(document_text))
        else:
            st.write(st.session_state.summary_text)

        st.write("------------------------------------------------------------------")
        st.download_button(
            label="Download Summary....",
            data=st.session_state.summary_text,
            file_name="summary.txt",
        )

    with tabs[1]:  # Previous Similar Judgments tab
        if "judgment_text" not in st.session_state:
            st.session_state.judgment_text = ""
            link = get_link(document_text)
            print(link)
            indian_kanoon_text = scrape_jina_ai(link)

            past_judgement_links = past_judgement_link(indian_kanoon_text)
            past_judgement_heading = get_past_judgement_heading(indian_kanoon_text)

            for i, q in enumerate(past_judgement_links):
                st.markdown(f"### Past Case Number: {i + 1}")
                st.session_state.judgment_text += f"### Past Case Number: {i + 1}"
                st.markdown(f"### Case Heading: {past_judgement_heading[i]}")
                st.session_state.judgment_text += f"### Case Heading: {past_judgement_heading[i]}"

                st.markdown(f'### Doc Link: {q.replace("https://r.jina.ai/", "")}')
                st.session_state.judgment_text += f'### Doc Link: {q.replace("https://r.jina.ai/", "")}'

                st.session_state.judgment_text += st.write_stream(get_similar_cases_summary(q))

                st.write("------------------------------------------------------------------")
                st.session_state.judgment_text += "------------------------------------------------------------------"

                st.session_state.judgment_text += "\n\n\n"

        else:
            st.write(st.session_state.judgment_text)
            st.write("------------------------------------------------------------------")

        st.download_button(
            label="Download Previous Judgements....",
            data="".join([str(element) for element in st.session_state.judgment_text]),
            file_name="previous_judgement.txt",
        )

    with tabs[2]:  # What Happened Next
        if "ST_maybe_text" not in st.session_state:
            st.session_state.ST_maybe_text = st.write_stream(ST_maybe(document_text))
        else:
            st.write(st.session_state.ST_maybe_text)

        st.write("------------------------------------------------------------------")
        st.download_button(
            label="Download ST_maybe....",
            data=st.session_state.ST_maybe_text,
            file_name="ST_maybe.txt",
        )

    with tabs[3]:  # Recording & Notes tab
        st.write("Recording and Notes Feature")

        # Initialize session state for recording and notes
        if "recording_done" not in st.session_state:
            st.session_state.recording_done = False
        if "user_notes" not in st.session_state:
            st.session_state.user_notes = ""

        # Recording Section
        if st.button("Start Recording"):
            if record_audio("output.wav", duration=5):  # Record for 5 seconds
                st.session_state.recording_done = True
                st.audio("output.wav", format='audio/wav')

        # Text Input Section (appears after recording is done)
        if st.session_state.recording_done:
            st.write("Add your notes below:")
            user_notes = st.text_area("Enter your notes here:", value=st.session_state.user_notes)

            if st.button("Save Notes"):
                st.session_state.user_notes = user_notes
                st.success("Notes saved successfully!")

            # Display saved notes
            if st.session_state.user_notes:
                st.write("### Your Saved Notes:")
                st.write(st.session_state.user_notes)

    st.header("Chat with PDF")
    index_name = st.text_input("Enter The Project Name(Always give unique project names)").strip().lower()

    if index_name:
        with st.spinner(f"Opening New Project {index_name}"):
            retriever = raptor_retriever_pinecone(document_text, index_name)
        if "messages" not in st.session_state:
            st.session_state.messages = []
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        user_question = st.text_input("Ask a question about the document:")
        if user_question:
            st.session_state.messages.append({"role": "user", "content": user_question})
            with st.chat_message("user"):
                st.markdown(user_question)

            with st.chat_message("assistant"):
                response = st.write_stream(raptor(retriever, user_question))

            st.session_state.messages.append({"role": "assistant", "content": response})