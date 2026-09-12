from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader, UnstructuredMarkdownLoader
import tempfile
import os

async def save_upload_file(upload_file):
    suffix = os.path.splitext(upload_file.filename)[1] # gets the suffix from uploaded file eg:- .pdf
# making a temporary file to store user input, delete = false if we do not do this then it would delete as loop ands
    with tempfile.NamedTemporaryFile(delete=False , suffix = suffix) as temp:
        contents = await upload_file.read()
        temp.write(contents)
        temp_path = temp.name

    return temp_path

def load_document(file_path):
    try :
        ext = file_path.lower()
        if ext.endswith(".pdf"):
            loader = PyPDFLoader(file_path=file_path)
        elif ext.endswith(".txt") or ext.endswith(".md"):
            loader = TextLoader(file_path=file_path, encoding="utf-8")
        elif ext.endswith(".docx"):
            loader = Docx2txtLoader(file_path=file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path}")
        docs = loader.load()
        return docs
    except Exception as e:
        print(f"Error loading document: {e}")
        raise

def chunking(docs):
        splitter = RecursiveCharacterTextSplitter(
            chunk_overlap=200,
            chunk_size=1000,
            separators=["\n\n","\n","."," "]
        )
        chunks = splitter.split_documents(docs)
        return chunks

async def process_document(upload_file):
    temp_path = await save_upload_file(upload_file)
    try:
        loader = load_document(temp_path)
        chunks = chunking(loader)
        return chunks
    finally:
        os.unlink(temp_path)