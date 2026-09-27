from fastapi import FastAPI

from app.config import settings
from app.controller.ai_controller import router as ai_router

app = FastAPI(
    title="Spring AI with Ollama - Text Analysis API",
    version="1.0.0",
    description=(
        "RESTful APIs for AI-powered text analysis including classification, "
        "sentiment analysis, summarization, and intent detection using Ollama with Llama models."
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

app.include_router(ai_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.SERVER_PORT, reload=True)
