from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, UnstructuredHTMLLoader, TextLoader, \
    UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from typing import List
from langchain_core.documents import Document
import pytesseract
from PIL import Image
import logging

logging.basicConfig(filename='app.log', level=logging.INFO)

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len)

embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embedding_function)


def load_and_split_document(file_path: str) -> List[Document]:
    if file_path.endswith('.pdf'):
        loader = PyPDFLoader(file_path)
        documents = loader.load()
    elif file_path.endswith('.docx'):
        loader = Docx2txtLoader(file_path)
        documents = loader.load()
    elif file_path.endswith('.html'):
        loader = UnstructuredHTMLLoader(file_path)
        documents = loader.load()
    elif file_path.endswith('.txt'):
        loader = TextLoader(file_path)
        documents = loader.load()
    elif file_path.endswith('.md'):
        loader = UnstructuredMarkdownLoader(file_path)
        documents = loader.load()
    elif file_path.endswith('.py'):
        loader = TextLoader(file_path)
        documents = loader.load()
    elif file_path.endswith(('.png', '.jpg', '.jpeg')):
        logging.info(f"Extracting text from image: {file_path}")
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image, lang='eng+rus')  # Поддержка английского и русского
            if not text.strip():
                logging.warning(f"No text extracted from image: {file_path}")
                return []
            documents = [Document(page_content=text, metadata={"source": file_path})]
        except Exception as e:
            logging.error(f"Error extracting text from image {file_path}: {str(e)}")
            return []
    else:
        raise ValueError(f"Unsupported file type: {file_path}")

    return text_splitter.split_documents(documents)


def index_document_to_chroma(file_path: str, file_id: int) -> bool:
    try:
        splits = load_and_split_document(file_path)
        logging.info(f"Indexing file: {file_path}, splits: {len(splits)}")

        for split in splits:
            split.metadata['file_id'] = file_id

        if not splits:
            logging.warning(f"No splits generated for file: {file_path}")
            return False

        vectorstore.add_documents(splits)
        logging.info(f"Successfully indexed file: {file_path}")
        return True
    except Exception as e:
        logging.error(f"Error indexing document {file_path}: {str(e)}")
        return False


def delete_doc_from_chroma(file_id: int):
    try:
        docs = vectorstore.get(where={"file_id": file_id})
        logging.info(f"Found {len(docs['ids'])} document chunks for file_id {file_id}")

        vectorstore._collection.delete(where={"file_id": file_id})
        logging.info(f"Deleted all documents with file_id {file_id}")
        return True
    except Exception as e:
        logging.error(f"Error deleting document with file_id {file_id} from Chroma: {str(e)}")
        return False