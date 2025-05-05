import streamlit as st
from api_utils import get_api_response

def display_chat_interface():
    # Chat container
    chat_container = st.container(border=True)
    
    with chat_container:
        for message in st.session_state.messages:
            avatar = "🧑" if message["role"] == "user" else "🤖"
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"])
    
        if prompt := st.chat_input("Введите ваш запрос...", key="chat_input"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="🧑"):
                st.markdown(prompt)
            
            with st.spinner("Генерация ответа..."):
                selected_model = st.session_state.get('selected_model', 'mistralai/mistral-7b-instruct:free')
                response = get_api_response(prompt, st.session_state.session_id, selected_model)
                
                if response:
                    st.session_state.session_id = response.get('session_id')
                    st.session_state.messages.append({"role": "assistant", "content": response['answer']})
                    
                    with st.chat_message("assistant", avatar="🤖"):
                        answer_parts = response['answer'].split("\n\n**Источник:**")
                        st.markdown(answer_parts[0])
                        if len(answer_parts) > 1:
                            st.info(f"**Источник:** {answer_parts[1]}")
                        
                        with st.expander("Подробности ответа"):
                            st.subheader("Сгенерированный ответ")
                            st.code(response['answer'])
                            st.subheader("Использованная модель")
                            st.code(response['model'])
                            st.subheader("ID сессии")
                            st.code(response['session_id'])
                else:
                    st.error("Не удалось получить ответ от API. Попробуйте снова.")