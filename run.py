import os
from dotenv import load_dotenv
from app import create_app
from app.utils.errors import register_error_handlers

# Load environment variables
load_dotenv()

# Create Flask application
app = create_app()

# Register error handlers
register_error_handlers(app)

if __name__ == '__main__':
    # Run the application
    app.run(host=os.environ.get('HOST', '0.0.0.0'),
            port=int(os.environ.get('PORT', 5000)),
            debug=os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't')) 