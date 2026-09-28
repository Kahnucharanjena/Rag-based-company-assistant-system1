import os

from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI


load_dotenv()


# ==========================================
# CONFIGURATION
# ==========================================

VECTORSTORE_PATH = "vectorstore"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY is not set in .env")


# ==========================================
# EMBEDDING MODEL
# ==========================================

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


# ==========================================
# GEMINI MODEL
# ==========================================

llm = ChatGoogleGenerativeAI(
    model="gemini-3.8-flash",
    google_api_key=GEMINI_API_KEY
)


# ==========================================
# CREATE VECTOR STORE
# ==========================================

def create_vectorstore(file_path, file_name):

    print("Loading PDF:", file_name)

    loader = PyPDFLoader(file_path)

    documents = loader.load()

    print("PDF pages:", len(documents))


    # Add source information

    for document in documents:

        document.metadata["source"] = file_name


    # Split document

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150
    )

    chunks = splitter.split_documents(documents)

    print("Created chunks:", len(chunks))


    # Create FAISS

    vectorstore = FAISS.from_documents(
        chunks,
        embeddings
    )


    # Save

    vectorstore.save_local(
        VECTORSTORE_PATH
    )

    print("Vector store created successfully.")

    return True


# ==========================================
# LOAD VECTOR STORE
# ==========================================

def load_vectorstore():

    if not os.path.exists(VECTORSTORE_PATH):

        raise FileNotFoundError(
            "Vector store does not exist. "
            "Please upload and process a PDF first."
        )


    vectorstore = FAISS.load_local(
        VECTORSTORE_PATH,
        embeddings,
        allow_dangerous_deserialization=True
    )

    return vectorstore


# ==========================================
# GREETING DETECTION
# ==========================================

def is_greeting(question):

    text = question.lower().strip()

    greetings = [
        "hi",
        "hii",
        "hiii",
        "hello",
        "hey",
        "heyy",
        "good morning",
        "good afternoon",
        "good evening",
        "good night",
        "how are you",
        "how r u"
    ]

    return text in greetings


# ==========================================
# ASK QUESTION
# ==========================================

def ask_question(question, chat_history=None):

    question = question.strip()


    # --------------------------------------
    # GREETING
    # --------------------------------------

    if is_greeting(question):

        return {
            "answer": (
                "Hello! 👋 Welcome to Customer Support. "
                "How can I help you today?"
            ),
            "sources": []
        }


    # --------------------------------------
    # LOAD VECTOR STORE
    # --------------------------------------

    vectorstore = load_vectorstore()


    # --------------------------------------
    # SEARCH DOCUMENT
    # --------------------------------------

    documents = vectorstore.similarity_search(
        question,
        k=4
    )


    if not documents:

        return {
            "answer": (
                "I couldn't find information about that "
                "in the available company documents."
            ),
            "sources": []
        }


    # --------------------------------------
    # BUILD CONTEXT
    # --------------------------------------

    context_parts = []

    sources = []


    for document in documents:

        page = document.metadata.get(
            "page",
            0
        )

        source = document.metadata.get(
            "source",
            "Unknown document"
        )


        context_parts.append(
            f"""
Source: {source}

Page: {page + 1}

Content:

{document.page_content}
"""
        )


        sources.append({
            "source": source,
            "page": page + 1
        })


    context = "\n\n".join(
        context_parts
    )


    # --------------------------------------
    # CHAT HISTORY
    # --------------------------------------

    history_text = ""


    if chat_history:

        for item in chat_history[-6:]:

            history_text += (
                f"User: {item.get('user', '')}\n"
                f"Assistant: {item.get('assistant', '')}\n"
            )


    # --------------------------------------
    # PROMPT
    # --------------------------------------

    prompt = f"""
You are a customer support assistant.

Answer the user's question using ONLY the
company document context provided below.

Do not invent information.

If the answer cannot be found in the
documents, say:

"I couldn't find that information in the
available company documents."

Be helpful and concise.

Conversation history:

{history_text}

Company document context:

{context}

User question:

{question}
"""


    # --------------------------------------
    # GEMINI
    # --------------------------------------

    response = llm.invoke(prompt)

    answer = response.content


    # --------------------------------------
    # CONVERT GEMINI RESPONSE TO TEXT
    # --------------------------------------

    if isinstance(answer, list):

        text_parts = []

        for item in answer:

            if isinstance(item, str):

                text_parts.append(item)

            elif isinstance(item, dict):

                if "text" in item:

                    text_parts.append(
                        str(item["text"])
                    )

        answer = "\n".join(text_parts)


    elif isinstance(answer, dict):

        if "text" in answer:

            answer = str(answer["text"])

        else:

            answer = str(answer)


    else:

        answer = str(answer)


    # --------------------------------------
    # RETURN RESULT
    # --------------------------------------

    return {
        "answer": answer,
        "sources": sources
    }