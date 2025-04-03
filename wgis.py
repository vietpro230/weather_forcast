import sys
path = '/home/viet'  # Your project directory
if path not in sys.path:
    sys.path.append(path)

from app import app as application