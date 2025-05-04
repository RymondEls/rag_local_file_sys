import streamlit as st
from api_utils import upload_document, list_documents, delete_document

def display_sidebar():
    # Sidebar: Model Selection
    st.sidebar.header("Выбор модели")
    available_models = [
        "mistralai/mistral-7b-instruct:free",
        "meta-llama/llama-3.2-3b-instruct:free",
        "meta-llama/llama-4-scout:free",
        "meta-llama/llama-4-maverick:free",
        "deepseek/deepseek-prover-v2:free",
        "tngtech/deepseek-r1t-chimera:free"
        "deepseek/deepseek-v3-base:free",
        "google/gemini-2.0-flash-exp:free",
        "google/gemini-flash-1.5-8b-exp"

    ]
    selected_model = st.sidebar.selectbox("Выберите модель:", available_models, index=0, key="selected_model")

    # Sidebar: Upload Document
    st.sidebar.header("Upload Document")
    uploaded_file = st.sidebar.file_uploader("Choose a file", type=["pdf", "docx", "html"])
    if uploaded_file is not None:
        if st.sidebar.button("Upload"):
            with st.spinner("Uploading..."):
                upload_response = upload_document(uploaded_file)
                if upload_response:
                    st.sidebar.success(
                        f"File '{uploaded_file.name}' uploaded successfully with ID {upload_response['file_id']}.")
                    st.session_state.documents = list_documents()  # Refresh the list after upload

    # Sidebar: List Documents
    st.sidebar.header("Uploaded Documents")
    if st.sidebar.button("Refresh Document List"):
        with st.spinner("Refreshing..."):
            st.session_state.documents = list_documents()

    # Initialize document list if not present
    if "documents" not in st.session_state:
        st.session_state.documents = list_documents()

    documents = st.session_state.documents
    if documents:
        for doc in documents:
            st.sidebar.text(f"{doc['filename']} (ID: {doc['id']}, Uploaded: {doc['upload_timestamp']})")

        # Delete Document
        selected_file_id = st.sidebar.selectbox("Select a document to delete", options=[doc['id'] for doc in documents],
                                                format_func=lambda x: next(
                                                    doc['filename'] for doc in documents if doc['id'] == x))
        if st.sidebar.button("Delete Selected Document"):
            with st.spinner("Deleting..."):
                delete_response = delete_document(selected_file_id)
                if delete_response:
                    st.sidebar.success(f"Document with ID {selected_file_id} deleted successfully.")
                    st.session_state.documents = list_documents()  # Refresh the list after deletion
                else:
                    st.sidebar.error(f"Failed to delete document with ID {selected_file_id}.")