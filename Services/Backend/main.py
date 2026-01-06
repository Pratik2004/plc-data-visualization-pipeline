from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="PLC Data Pipeline API",
    version="1.0.0",
    description="Local-first PLC data ingestion and visualization",
)

# CORS is required so the React UI can call the API from another port later.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "PLC Data Pipeline API v1.0"}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "backend", "version": "1.0.0"}
