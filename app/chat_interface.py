import streamlit as st
from api_utils import get_api_response

def display_chat_interface():
    # Chat interface
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Query:"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Generating response..."):
            # Используем модель из session_state
            selected_model = st.session_state.get('selected_model', 'mistralai/mistral-7b-instruct:free')
            response = get_api_response(prompt, st.session_state.session_id, selected_model)

            if response:
                st.session_state.session_id = response.get('session_id')
                st.session_state.messages.append({"role": "assistant", "content": response['answer']})

                with st.chat_message("assistant"):
                    # Разделяем ответ на основную часть и источник
                    answer_parts = response['answer'].split("\n\n**Источник:**")
                    st.markdown(answer_parts[0])  # Основной ответ
                    if len(answer_parts) > 1:
                        st.info(f"**Источник:** {answer_parts[1]}")  # Источник

                    with st.expander("Details"):
                        st.subheader("Generated Answer")
                        st.code(response['answer'])
                        st.subheader("Model Used")
                        st.code(response['model'])
                        st.subheader("Session ID")
                        st.code(response['session_id'])
            else:
                st.error("Failed to get a response from the API. Please try again.")