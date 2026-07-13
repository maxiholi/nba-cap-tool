from fastapi import FastAPI

app = FastAPI(title="NBA Cap Engine")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}