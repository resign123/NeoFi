from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.event import Event
from app.models.permission import Permission, RoleType
from app.models.user import User
from app.utils.decorators import owner_required
from app.utils.validators import PermissionSchema
from app.utils.errors import ValidationError, ResourceNotFoundError, AuthorizationError
from marshmallow import ValidationError as MarshmallowValidationError

collab_bp = Blueprint('collaboration', __name__)

@collab_bp.route('/<int:id>/share', methods=['POST'])
@owner_required
def share_event(id, permission=None):
    """Share an event with other users."""
    try:
        user_id = get_jwt_identity()
        event = Event.query.get(id)
        
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        
        # Validate data
        schema = PermissionSchema(many=True)
        data = schema.load(request.get_json().get('users', []))
        
        created_permissions = []
        
        for user_permission in data:
            # Check if user exists
            target_user = User.query.get(user_permission['user_id'])
            if not target_user:
                return jsonify({'error': f'User with ID {user_permission["user_id"]} not found'}), 404
            
            # Check if permission already exists
            existing_permission = Permission.query.filter_by(
                event_id=id,
                user_id=user_permission['user_id']
            ).first()
            
            # Create or update permission
            if existing_permission:
                existing_permission.role = RoleType(user_permission['role'])
                existing_permission.granted_by = user_id
                created_permissions.append(existing_permission)
            else:
                new_permission = Permission(
                    event_id=id,
                    user_id=user_permission['user_id'],
                    role=RoleType(user_permission['role']),
                    granted_by=user_id
                )
                db.session.add(new_permission)
                created_permissions.append(new_permission)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Event shared successfully',
            'permissions': [perm.to_dict() for perm in created_permissions]
        }), 200
    
    except MarshmallowValidationError as e:
        return jsonify({'error': str(e)}), 400
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@collab_bp.route('/<int:id>/permissions', methods=['GET'])
@jwt_required()
def get_permissions(id):
    """List all permissions for an event."""
    try:
        user_id = get_jwt_identity()
        
        # Check if user has permission to view this event
        permission = Permission.query.filter_by(
            event_id=id,
            user_id=user_id
        ).first()
        
        if not permission:
            return jsonify({'error': 'You do not have permission to view this event'}), 403
        
        # Get all permissions for the event
        permissions = Permission.query.filter_by(event_id=id).all()
        
        return jsonify({
            'permissions': [perm.to_dict() for perm in permissions]
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@collab_bp.route('/<int:id>/permissions/<int:user_id>', methods=['PUT'])
@owner_required
def update_permission(id, user_id, permission=None):
    """Update permissions for a user."""
    try:
        current_user_id = get_jwt_identity()
        
        # Check if target user exists
        target_user = User.query.get(user_id)
        if not target_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if permission exists
        target_permission = Permission.query.filter_by(
            event_id=id,
            user_id=user_id
        ).first()
        
        if not target_permission:
            return jsonify({'error': 'Permission not found'}), 404
        
        # Validate data
        schema = PermissionSchema()
        data = schema.load(request.get_json())
        
        # Check if trying to change owner role
        if target_permission.role == RoleType.OWNER and data['role'] != 'owner':
            # Check if there would be at least one owner left
            owners = Permission.query.filter_by(
                event_id=id,
                role=RoleType.OWNER
            ).all()
            
            if len(owners) <= 1:
                return jsonify({'error': 'Cannot remove the last owner. Transfer ownership first.'}), 400
        
        # Update permission
        target_permission.role = RoleType(data['role'])
        target_permission.granted_by = current_user_id
        
        db.session.commit()
        
        return jsonify({
            'message': 'Permission updated successfully',
            'permission': target_permission.to_dict()
        }), 200
    
    except MarshmallowValidationError as e:
        return jsonify({'error': str(e)}), 400
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@collab_bp.route('/<int:id>/permissions/<int:user_id>', methods=['DELETE'])
@owner_required
def remove_permission(id, user_id, permission=None):
    """Remove access for a user."""
    try:
        # Check if target user exists
        target_user = User.query.get(user_id)
        if not target_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if permission exists
        target_permission = Permission.query.filter_by(
            event_id=id,
            user_id=user_id
        ).first()
        
        if not target_permission:
            return jsonify({'error': 'Permission not found'}), 404
        
        # Check if trying to remove owner
        if target_permission.role == RoleType.OWNER:
            # Check if there would be at least one owner left
            owners = Permission.query.filter_by(
                event_id=id,
                role=RoleType.OWNER
            ).all()
            
            if len(owners) <= 1:
                return jsonify({'error': 'Cannot remove the last owner. Transfer ownership first.'}), 400
        
        # Remove permission
        db.session.delete(target_permission)
        db.session.commit()
        
        return jsonify({
            'message': 'Permission removed successfully'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500 