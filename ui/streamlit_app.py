import requests
import streamlit as st

API_URL = "http://localhost:8000"

st.set_page_config(page_title="ClauseWise", page_icon="⚖️", layout="wide")
st.title("⚖️ ClauseWise — Contract Q&A & Review")

with st.sidebar:
    st.header("Upload a contract")
    uploaded = st.file_uploader("PDF or DOCX", type=["pdf", "docx"])
    if uploaded and st.button("Ingest"):
        response = requests.post(
            f"{API_URL}/documents/upload",
            files={"file": (uploaded.name, uploaded.getvalue())},
            timeout=120,
        )
        if response.ok:
            st.session_state.document_id = response.json()["document_id"]
            st.success(f"Uploaded: {uploaded.name}")
        else:
            st.error(response.json().get("detail", "Upload failed"))

document_id = st.session_state.get("document_id")
if not document_id:
    st.info("Upload a contract in the sidebar to get started.")
    st.stop()

question = st.chat_input("Ask a question about the contract...")
if question:
    with st.chat_message("user"):
        st.write(question)
    response = requests.post(
        f"{API_URL}/chat",
        json={"document_id": document_id, "question": question},
        timeout=120,
    )
    with st.chat_message("assistant"):
        if response.ok:
            data = response.json()
            st.write(data["answer"])
            for citation in data["citations"]:
                with st.expander(f"📎 {citation.get('section') or 'Source'} (score {citation['score']:.2f})"):
                    st.write(citation["text"])
        else:
            st.warning(response.json().get("detail", "Request failed"))
