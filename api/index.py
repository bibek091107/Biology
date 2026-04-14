import os
import sys

# Add the parent directory to Python's modules path so app.py can be found
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Vercel requires the application to be named "app" in the file that it loads.
if __name__ == "__main__":
    app.run()
