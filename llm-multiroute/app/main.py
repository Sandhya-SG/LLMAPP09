from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.controller.ai_controller import router as ai_router

app = FastAPI(
    title="Multi-Route LLM API",
    version="1.0.0",
    description=(
        "RESTful APIs for AI-powered text analysis that routes each NLP task "
        "(classify, sentiment, summarize, intent) to a different Ollama model. "
        "Each task type is configurable via environment variables."
    ),
    docs_url="/swagger-ui.html",
    openapi_url="/api-docs",
    contact={
        "name": "AI API Support",
        "email": "support@example.com",
    },
    servers=[
        {"url": f"http://localhost:{settings.SERVER_PORT}", "description": "Local Development Server"}
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.SERVER_PORT, reload=True)
