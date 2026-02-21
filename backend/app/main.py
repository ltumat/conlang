from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import languages

app = FastAPI(
    title="Conlang API",
    description="Backend API for Conlang - a vocabulary learning app focused on providing context",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

app.include_router(languages.router)