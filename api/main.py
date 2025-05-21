from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic_models import QueryInput, QueryResponse, DocumentInfo, DeleteFileRequest
from langchain_utils import get_rag_chain, retriever
from db_utils import insert_application_logs, get_chat_history, get_all_documents, insert_document_record, delete_document_record, get_filename_by_id
from chroma_utils import index_document_to_chroma, delete_doc_from_chroma, embedding_function
import os
import uuid
import logging
import shutil
import numpy as np

logging.basicConfig(filename='app.log', level=logging.INFO)

app = FastAPI()

# Создать директорию temp, если она не существует
os.makedirs("temp", exist_ok=True)

def cosine_similarity(vec1, vec2):
    """Вычисляет косинусное сходство между двумя векторами."""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    dot_product = np.dot(vec1, vec2)
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)
    if norm_vec1 == 0 or norm_vec2 == 0:
        return 0.0
    return dot_product / (norm_vec1 * norm_vec2)

@app.post("/chat", response_model=QueryResponse)
def chat(query_input: QueryInput):
    session_id = query_input.session_id or str(uuid.uuid4())
    logging.info(f"Session ID: {session_id}, User Query: {query_input.question}, Model: {query_input.model}")

    chat_history = get_chat_history(session_id)
    rag_chain = get_rag_chain(model=query_input.model)

    # Извлекаем предыдущее сообщение пользователя и ответ LLM
    previous_user_message = None
    previous_llm_response = None
    if len(chat_history) >= 2:  # Проверяем, есть ли хотя бы одно сообщение и ответ
        # История чата: [{"role": "human", "content": "..."}, {"role": "ai", "content": "..."}, ...]
        for i in range(len(chat_history) - 2, -1, -2):  # Идём с конца, шаг 2
            if chat_history[i]["role"] == "human" and chat_history[i + 1]["role"] == "ai":
                previous_user_message = chat_history[i]["content"]
                previous_llm_response = chat_history[i + 1]["content"]
                break

    # Формируем текст для эмбеддинга с учётом контекста
    text_to_embed = query_input.question
    context_similarity_threshold = 0.6  # Порог сходства для учёта контекста

    if previous_user_message and previous_llm_response:
        # Вычисляем эмбеддинги для текущего и предыдущего сообщения
        current_embedding = embedding_function.embed_query(query_input.question)
        previous_embedding = embedding_function.embed_query(previous_user_message)

        # Проверяем сходство между текущим и предыдущим сообщением
        similarity = cosine_similarity(current_embedding, previous_embedding)
        logging.info(f"Similarity between current and previous message: {similarity:.3f}")

        if similarity >= context_similarity_threshold:
            # Если сообщения связаны, добавляем контекст
            text_to_embed = f"Previous user message: {previous_user_message}\nPrevious LLM response: {previous_llm_response}\nCurrent user message: {query_input.question}"
            logging.info("Context included in embedding due to high similarity.")
        else:
            logging.info("Context ignored due to low similarity (different topic).")

    # Получаем эмбеддинг текста (с учётом контекста, если он добавлен)
    query_embedding = embedding_function.embed_query(text_to_embed)

    # Вызываем RAG-цепочку для генерации ответа
    result = rag_chain.invoke({
        "input": query_input.question,
        "chat_history": chat_history
    })
    answer = result['answer']

    # Получаем релевантные документы
    context = retriever.get_relevant_documents(query_input.question)

    file_ids = set()
    similarity_threshold = 0.25  # Порог сходства для документов

    for doc in context:
        file_id = doc.metadata.get('file_id')
        if file_id:
            doc_embedding = embedding_function.embed_documents([doc.page_content])[0]
            similarity = cosine_similarity(query_embedding, doc_embedding)
            if similarity >= similarity_threshold:
                file_ids.add(file_id)
                logging.info(f"Document with file_id {file_id} included: similarity = {similarity:.3f}")
            else:
                logging.info(f"Document with file_id {file_id} filtered out: similarity = {similarity:.3f}")

    filenames = [get_filename_by_id(file_id) for file_id in file_ids]
    filenames = [name for name in filenames if name]

    if filenames:
        answer += f"\n\n**Источник:** Ответ основан на информации из следующих файлов: {', '.join(filenames)}."

    insert_application_logs(session_id, query_input.question, answer, query_input.model)
    logging.info(f"Session ID: {session_id}, AI Response: {answer}, Model: {query_input.model}")
    return QueryResponse(answer=answer, session_id=session_id, model=query_input.model)

@app.post("/upload-doc")
def upload_and_index_document(file: UploadFile = File(...)):
    allowed_extensions = ['.pdf', '.docx', '.html', '.txt', '.md', '.py', '.png', '.jpg', '.jpeg']
    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed types are: {', '.join(allowed_extensions)}")

    max_file_size = 10 * 1024 * 1024  # 10 MB
    if file.size > max_file_size:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit.")
    if file.size == 0:
        raise HTTPException(status_code=400, detail="File is empty.")

    temp_file_path = os.path.join("temp", f"temp_{file.filename}")

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_id = insert_document_record(file.filename)
        success = index_document_to_chroma(temp_file_path, file_id)

        if success:
            return {"message": f"File {file.filename} has been successfully uploaded and indexed.", "file_id": file_id}
        else:
            delete_document_record(file_id)
            raise HTTPException(status_code=500, detail=f"Failed to index {file.filename}. Possibly no text could be extracted from the image.")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
@app.get("/list-docs", response_model=list[DocumentInfo])
def list_documents():
    return get_all_documents()

@app.post("/delete-doc")
def delete_document(request: DeleteFileRequest):
    chroma_delete_success = delete_doc_from_chroma(request.file_id)

    if chroma_delete_success:
        db_delete_success = delete_document_record(request.file_id)
        if db_delete_success:
            return {"message": f"Successfully deleted document with file_id {request.file_id} from the system."}
        else:
            return {"error": f"Deleted from Chroma but failed to delete document with file_id {request.file_id} from the database."}
    else:
        return {"error": f"Failed to delete document with file_id {request.file_id} from Chroma."}