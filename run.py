import uvicorn
import os

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    print(f"\nStarting Campus Mental Health Early Warning System at http://{host}:{port}")
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
