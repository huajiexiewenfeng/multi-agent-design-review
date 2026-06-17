from fastapi import FastAPI

from backend.app.api import router as api_router

app = FastAPI(title="Multi-Agent Design Review Workbench")
app.include_router(api_router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
