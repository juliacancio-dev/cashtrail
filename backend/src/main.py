from fastapi import FastAPI

app = FastAPI(title="CashTrail API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
