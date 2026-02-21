from fastapi import FastAPI

app = FastAPI(
    title="Conlang API",
    description="Backend API for Conlang - a vocabulary learning app focused on providing context",
    version="0.1.0",
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
