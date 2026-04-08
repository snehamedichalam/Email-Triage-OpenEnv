import uvicorn
# Import the FastAPI app instance from your main.py file
from server.main import app 

def main():
    """
    The entry point called by the 'server' script in pyproject.toml
    """
    # Note: we point uvicorn to server.main:app now
    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, reload=False)

if __name__ == "__main__":
    main()