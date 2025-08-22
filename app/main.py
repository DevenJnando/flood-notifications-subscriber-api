from fastapi import FastAPI
import uvicorn
import logging

from app.routes import subscribers, postcodes

app: FastAPI = FastAPI()
logger = logging.getLogger("uvicorn.info")

app.include_router(subscribers.router)
app.include_router(postcodes.router)

if __name__ == "__main__":
    uvicorn.run(app, log_level="info")
