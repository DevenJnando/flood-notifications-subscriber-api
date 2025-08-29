from fastapi import FastAPI
import uvicorn

from app.routes import subscribers

app: FastAPI = FastAPI()

app.include_router(subscribers.router)

if __name__ == "__main__":
    uvicorn.run(app)
