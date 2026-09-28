import os
import uuid

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from rag import create_vectorstore, ask_question


app = FastAPI(
    title="Customer Support RAG API"
)


# ==========================================
# CORS
# ==========================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ==========================================
# DIRECTORIES
# ==========================================

UPLOAD_DIR = "data/documents"

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)


# ==========================================
# CHAT SESSIONS
# ==========================================

sessions = {}


# ==========================================
# HEALTH CHECK
# ==========================================

@app.get("/api/health")
def health():

    return {
        "status": "online"
    }


# ==========================================
# UPLOAD PDF
# ==========================================

@app.post("/api/upload")
async def upload_document(
    file: UploadFile = File(...)
):

    try:

        if not file.filename.lower().endswith(".pdf"):

            raise HTTPException(
                status_code=400,
                detail="Only PDF files are allowed."
            )


        file_path = os.path.join(
            UPLOAD_DIR,
            file.filename
        )


        contents = await file.read()


        with open(
            file_path,
            "wb"
        ) as f:

            f.write(contents)


        print(
            "Saved PDF:",
            file_path
        )


        # Create vector store

        create_vectorstore(
            file_path,
            file.filename
        )


        return {
            "success": True,
            "message": "Document processed successfully!",
            "filename": file.filename
        }


    except HTTPException:

        raise


    except Exception as e:

        print(
            "UPLOAD ERROR:",
            repr(e)
        )


        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ==========================================
# CHAT
# ==========================================

@app.post("/api/chat")
async def chat(data: dict):

    try:

        question = data.get(
            "message",
            ""
        ).strip()


        session_id = data.get(
            "session_id",
            str(uuid.uuid4())
        )


        if not question:

            raise HTTPException(
                status_code=400,
                detail="Message cannot be empty."
            )


        if session_id not in sessions:

            sessions[session_id] = []


        history = sessions[session_id]


        print(
            "QUESTION:",
            question
        )


        result = ask_question(
            question,
            history
        )


        # Save conversation

        history.append({
            "user": question,
            "assistant": result["answer"]
        })


        # Keep last 10 conversations

        sessions[session_id] = history[-10:]


        return {
            "success": True,

            "answer": result["answer"],

            "sources": result.get(
                "sources",
                []
            ),

            "session_id": session_id
        }


    except HTTPException:

        raise


    except Exception as e:

        print(
            "CHAT ERROR:",
            repr(e)
        )


        raise HTTPException(
            status_code=500,
            detail=str(e)
        )