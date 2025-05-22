from flask import jsonify
import traceback

class APIError(Exception):
    """Base exception class for API errors."""
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        rv = dict(self.payload or ())
        rv['error'] = self.message
        return rv

class ResourceNotFoundError(APIError):
    """Exception raised when a resource is not found."""
    def __init__(self, message="Resource not found", payload=None):
        super().__init__(message, status_code=404, payload=payload)

class AuthenticationError(APIError):
    """Exception raised for authentication errors."""
    def __init__(self, message="Authentication failed", payload=None):
        super().__init__(message, status_code=401, payload=payload)

class AuthorizationError(APIError):
    """Exception raised for authorization errors."""
    def __init__(self, message="Insufficient permissions", payload=None):
        super().__init__(message, status_code=403, payload=payload)

class ValidationError(APIError):
    """Exception raised for validation errors."""
    def __init__(self, message="Validation failed", payload=None):
        super().__init__(message, status_code=400, payload=payload)

class ConflictError(APIError):
    """Exception raised for conflicts."""
    def __init__(self, message="Resource conflict", payload=None):
        super().__init__(message, status_code=409, payload=payload)

def register_error_handlers(app):
    """Register error handlers with the Flask app."""
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        return jsonify({'error': 'Method not allowed'}), 405
    
    @app.errorhandler(500)
    def handle_internal_server_error(error):
        # Log the error here
        return jsonify({
            'error': 'Internal server error',
            'message': str(error)
        }), 500
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        # Log the error for debugging
        traceback.print_exc()
        return jsonify({
            'error': 'An unexpected error occurred',
            'message': str(error)
        }), 500 