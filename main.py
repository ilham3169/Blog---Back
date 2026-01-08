from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, blogs

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(blogs.router)