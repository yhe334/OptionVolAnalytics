from fastapi import FastAPI
from iv_hv_analytics.api.routes.volatility import router as volatility_router
from iv_hv_analytics.persistence.db import init_db 

app = FastAPI(title = 'IV vs HV Analytics Service',version = '0.1.0')
app.include_router(volatility_router)

@app.on_event("startup")
def on_startup():
    init_db()



@app.get("/health")
def health():
    return {"status": "ok"}

