# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
from app import db
from app.models.event import Event
from app.models.permission import Permission, RoleType
from app.models.version import EventVersion, ChangeLog
from app.utils.decorators import jwt_required_with_role, editor_required
from app.utils.errors import ValidationError, ResourceNotFoundError, AuthorizationError
from marshmallow import ValidationError as MarshmallowValidationError
from datetime import datetime


version_bp = Blueprint('versioning', __name__)


@version_bp.route('/<int:id>/history', methods=['GET'])
@jwt_required_with_role(['owner', 'editor', 'viewer'])
def get_event_history(id, permission=None):
    """Get version history for an event."""
    try:
        event = Event.query.get(id)

        if not event:
            return jsonify({'error': 'Event not found'}), 404

        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)

        versions = EventVersion.query.filter_by(event_id=id).order_by(EventVersion.version_number.desc()).paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'versions': [version.to_dict() for version in versions.items],
            'total': versions.total,
            'pages': versions.pages,
            'page': page,
            'per_page': per_page
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@version_bp.route('/<int:id>/history/<int:version_id>', methods=['GET'])
@jwt_required_with_role(['owner', 'editor', 'viewer'])
def get_specific_version(id, version_id, permission=None):
    """Get a specific version of an event."""
    try:
        event = Event.query.get(id)

        if not event:
            return jsonify({'error': 'Event not found'}), 404

        version = EventVersion.query.filter_by(
            event_id=id,
            version_number=version_id
        ).first()

        if not version:
            return jsonify({'error': 'Version not found'}), 404

        return jsonify(version.to_dict()), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@version_bp.route('/<int:id>/rollback/<int:version_id>', methods=['POST'])
@editor_required
def rollback_event(id, version_id, permission=None):
    """Rollback to a previous version."""
    try:
        user_id = get_jwt_identity()
        event = Event.query.get(id)

        if not event:
            return jsonify({'error': 'Event not found'}), 404

        target_version = EventVersion.query.filter_by(
            event_id=id,
            version_number=version_id
        ).first()

        if not target_version:
            return jsonify({'error': 'Version not found'}), 404

        current_version = event.create_version(user_id)
        db.session.add(current_version)

        version_data = target_version.get_data_dict()

        event.title = version_data.get('title', event.title)
        event.description = version_data.get('description', event.description)
        event.start_time = datetime.fromisoformat(version_data.get('start_time')) if 'start_time' in version_data else event.start_time
        event.end_time = datetime.fromisoformat(version_data.get('end_time')) if 'end_time' in version_data else event.end_time
        event.location = version_data.get('location', event.location)
        event.is_recurring = version_data.get('is_recurring', event.is_recurring)

        changelog = current_version.diff_with(target_version)
        db.session.add(changelog)

        db.session.commit()

        return jsonify({
            'message': 'Event rolled back successfully',
            'event': event.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@version_bp.route('/<int:id>/changelog', methods=['GET'])
@jwt_required_with_role(['owner', 'editor', 'viewer'])
def get_event_changelog(id, permission=None):
    """Get a chronological log of all changes to an event."""
    try:
        event = Event.query.get(id)

        if not event:
            return jsonify({'error': 'Event not found'}), 404

        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)

        # Get all change logs for this event
        changelogs = ChangeLog.query.filter_by(event_id=id).order_by(ChangeLog.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'changelogs': [log.to_dict() for log in changelogs.items],
            'total': changelogs.total,
            'pages': changelogs.pages,
            'page': page,
            'per_page': per_page
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@version_bp.route('/<int:id>/compare', methods=['GET'])
@jwt_required_with_role(['owner', 'editor', 'viewer'])
def compare_versions(id, permission=None):
    """Compare two versions of an event."""
    try:
        event = Event.query.get(id)

        if not event:
            return jsonify({'error': 'Event not found'}), 404

        from_version = request.args.get('from', type=int)
        to_version = request.args.get('to', type=int)

        if not from_version or not to_version:
            return jsonify({'error': 'Both from_version and to_version parameters are required'}), 400

        source_version = EventVersion.query.filter_by(
            event_id=id,
            version_number=from_version
        ).first()

        target_version = EventVersion.query.filter_by(
            event_id=id,
            version_number=to_version
        ).first()

        if not source_version or not target_version:
            return jsonify({'error': 'One or both versions not found'}), 404

        # Create a diff between the two versions
        diff = source_version.diff_with(target_version).to_dict()

        return jsonify({
            'comparison': diff,
            'from_version': from_version,
            'to_version': to_version
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500