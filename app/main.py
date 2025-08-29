from fastapi import FastAPI
import uvicorn

from app.routes import subscribers, postcodes

app: FastAPI = FastAPI()

app.include_router(subscribers.router)
app.include_router(postcodes.router)

if __name__ == "__main__":
    uvicorn.run(app)
