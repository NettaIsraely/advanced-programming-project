from fastapi import FastAPI

from tlvflow.api.routes import router

app = FastAPI(title="TLVFlow API")
app.include_router(router)
