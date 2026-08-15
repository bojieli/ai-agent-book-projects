import uvicorn
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()
    import main
    uvicorn.run(main.app, host="0.0.0.0", port=9999)
