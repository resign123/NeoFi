from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.models.permission import Permission, RoleType
from app import db

def jwt_required_with_role(roles=None):
    """
    Check if JWT token is present and valid, and if user has the required role.
    :param roles: List of roles allowed to access the endpoint
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            
            # If no specific roles required, just return
            if not roles:
                return fn(*args, **kwargs)
            
            # If event_id is in path params, check role for that event
            event_id = kwargs.get('id')
            if not event_id:
                # If no event_id in path, assume it's a generic endpoint
                return fn(*args, **kwargs)
            
            # Get permission
            permission = Permission.query.filter_by(
                event_id=event_id,
                user_id=user_id
            ).first()
            
            if not permission or permission.role.value not in roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            # Add permission to kwargs for use in endpoint
            kwargs['permission'] = permission
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def admin_required(fn):
    """Check if user is admin (not used in this application but included for extensibility)."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        # Here we would check if user is admin
        # For now, just pass-through
        return fn(*args, **kwargs)
    return wrapper

def validate_json(*expected_args):
    """Validate if the expected arguments are in the request JSON."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No JSON data provided'}), 400
            
            missing = [arg for arg in expected_args if arg not in data]
            if missing:
                return jsonify({'error': f'Missing required fields: {", ".join(missing)}'}), 400
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def owner_required(fn):
    """Check if user is the owner of the event."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        event_id = kwargs.get('id')
        
        permission = Permission.query.filter_by(
            event_id=event_id,
            user_id=user_id
        ).first()
        
        if not permission or permission.role != RoleType.OWNER:
            return jsonify({'error': 'Only the owner can perform this action'}), 403
        
        kwargs['permission'] = permission
        return fn(*args, **kwargs)
    return wrapper

def editor_required(fn):
    """Check if user is an editor or owner of the event."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        event_id = kwargs.get('id')
        
        permission = Permission.query.filter_by(
            event_id=event_id,
            user_id=user_id
        ).first()
        
        if not permission or not permission.can_edit():
            return jsonify({'error': 'Editor or owner permissions required'}), 403
        
        kwargs['permission'] = permission
        return fn(*args, **kwargs)
    return wrapper 