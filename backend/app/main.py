from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router

app = FastAPI(title="Indian Railways Delay Intelligence System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return {"message": "Indian Railways Delay Intelligence System API"}
