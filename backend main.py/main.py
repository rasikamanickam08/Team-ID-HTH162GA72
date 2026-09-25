from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil

from analyzer import analyze_documents

app = FastAPI(
    title="COMPLYAI API",
    description="AI Compliance Command Center Backend",
    version="1.0.0"
)

# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/")
def home():
    return {
        "status": "online",
        "message": "COMPLYAI backend is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/scan")
async def scan_compliance(
    regulation: UploadFile = File(...),
    policy: UploadFile = File(...)
):

    if not regulation.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Regulation file must be a PDF"
        )

    if not policy.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Company policy file must be a PDF"
        )

    regulation_path = os.path.join(
        UPLOAD_DIR,
        "regulation.pdf"
    )

    policy_path = os.path.join(
        UPLOAD_DIR,
        "policy.pdf"
    )

    try:

        with open(regulation_path, "wb") as buffer:
            shutil.copyfileobj(
                regulation.file,
                buffer
            )

        with open(policy_path, "wb") as buffer:
            shutil.copyfileobj(
                policy.file,
                buffer
            )

        result = analyze_documents(
            regulation_path,
            policy_path
        )

        return result

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000
    )