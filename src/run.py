import uvicorn
from app.config import settings
from app.database.models import init_db

if __name__ == "__main__":
    # Initialize database
    print("Initializing database...")
    init_db()
    print("Database initialized!")
    
    # Run application
    print(f"Starting server on {settings.API_HOST}:{settings.API_PORT}")
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )