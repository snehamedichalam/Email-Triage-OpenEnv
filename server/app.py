import uvicorn
from fastapi import FastAPI
from openenv_core import OpenEnv # Optional but good to import if using

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Email Triage Server Ready"}

# FIX: server/app.py must have a main() function
def main():
    """
    The entry point called by the 'server' script in pyproject.toml
    """
    uvicorn.run("server.app:app", host="0.0.0.0", port=8000, reload=False)

# FIX: main() function not callable (missing if __name__ == '__main__')
if __name__ == "__main__":
    main()