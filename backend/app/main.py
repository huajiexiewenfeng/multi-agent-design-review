from fastapi import FastAPI

app = FastAPI(title="Multi-Agent Design Review Workbench")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
