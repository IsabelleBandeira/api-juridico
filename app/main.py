from fastapi import FastAPI

app = FastAPI(
    title="API Jurídico",
    description="API para consulta de autores, acordos e documentos.",
    version="1.0.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}