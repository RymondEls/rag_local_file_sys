import streamlit as st
from api_utils import upload_document, list_documents, delete_document

def display_sidebar():
    with st.sidebar:
        # Sidebar header
        st.header("Настройки чатбота")
        st.divider()

        # Model Selection Section
        with st.expander("Выбор модели", expanded=True):
            st.subheader("Модель ИИ")
            available_models = [
                "mistralai/mistral-7b-instruct:free",
                "meta-llama/llama-3.2-3b-instruct:free",
                "meta-llama/llama-4-scout:free",
                "meta-llama/llama-4-maverick:free",
                "deepseek/deepseek-prover-v2:free",
                "tngtech/deepseek-r1t-chimera:free",
                "deepseek/deepseek-v3-base:free",
                "google/gemini-2.0-flash-exp:free",
                "google/gemini-flash-1.5-8b-exp"
            ]
            selected_model = st.selectbox(
                "Выберите модель:",
                available_models,
                index=0,
                key="selected_model",
                help="Выберите модель ИИ для ответов."
            )

        st.divider()

        # File Upload Section
        with st.expander("Загрузка документа", expanded=True):
            st.subheader("Добавить файл")
            uploaded_file = st.file_uploader(
                "Перетащите или выберите файл",
                type=["pdf", "docx", "html", "txt", "md", "py", "png", "jpg", "jpeg"],
                key="file_uploader",
                help="Поддерживаемые форматы: PDF, DOCX, HTML, TXT, Markdown, Python, PNG, JPG, JPEG"
            )
            if uploaded_file is not None:
                if st.button("Загрузить", key="upload_button", type="primary"):
                    with st.spinner("Загрузка..."):
                        upload_response = upload_document(uploaded_file)
                        if upload_response:
                            st.success(
                                f"Файл '{uploaded_file.name}' успешно загружен с ID {upload_response['file_id']}."
                            )
                            st.session_state.documents = list_documents()
                        else:
                            st.error("Не удалось загрузить файл.")

        st.divider()

        # Document Management Section
        with st.expander("Управление документами", expanded=True):
            st.subheader("Список документов")
            if st.button("Обновить список", key="refresh_button", type="primary"):
                with st.spinner("Обновление..."):
                    st.session_state.documents = list_documents()

            if "documents" not in st.session_state:
                st.session_state.documents = list_documents()

            documents = st.session_state.documents
            if documents:
                for doc in documents:
                    st.write(f"{doc['filename']} (ID: {doc['id']}, Загружен: {doc['upload_timestamp']})")

                selected_file_id = st.selectbox(
                    "Выберите документ для удаления",
                    options=[doc['id'] for doc in documents],
                    format_func=lambda x: next(doc['filename'] for doc in documents if doc['id'] == x),
                    key="delete_select"
                )
                if st.button("Удалить документ", key="delete_button", type="secondary"):
                    with st.spinner("Удаление..."):
                        delete_response = delete_document(selected_file_id)
                        if delete_response:
                            st.success(f"Документ с ID {selected_file_id} успешно удалён.")
                            st.session_state.documents = list_documents()
                        else:
                            st.error(f"Не удалось удалить документ с ID {selected_file_id}.")
            else:
                st.info("Документы пока не загружены.")