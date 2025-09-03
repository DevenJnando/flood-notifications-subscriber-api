from fastapi import FastAPI
import uvicorn

from app.routes import subscribers

app: FastAPI = FastAPI()

app.include_router(subscribers.router)


@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Welcome to this app!"}


if __name__ == "__main__":
    uvicorn.run(app)
