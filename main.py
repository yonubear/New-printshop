import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

from app import app

if __name__ == "__main__":
    # Get port from environment or use 5000 as default
    port = int(os.environ.get("PORT", 5000))
    # In production, set debug to False
    debug = os.environ.get("FLASK_ENV") == "development"
    
    app.run(host="0.0.0.0", port=port, debug=debug)
