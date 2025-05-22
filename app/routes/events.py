# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from app.models.event import Event, RecurrencePattern, RecurrenceType
from app.models.permission import Permission, RoleType
from app.models.user import User
from app.utils.decorators import editor_required, owner_required, jwt_required_with_role
from app.utils.validators import EventSchema, BatchEventSchema
from app.utils.errors import ValidationError, ResourceNotFoundError, AuthorizationError, ConflictError
from marshmallow import ValidationError as MarshmallowValidationError
from sqlalchemy.exc import IntegrityError
import json

events_bp = Blueprint('events', __name__)

@events_bp.route('', methods=['POST'])
@jwt_required()
def create_event():
    """Create a new event."""
    try:
        user_id = get_jwt_identity()

        user_id_int = int(user_id) if isinstance(user_id, str) else user_id

        json_data = request.get_json()
        if not json_data:
            return jsonify({'error': 'No JSON data provided'}), 400

        schema = EventSchema()
        data = schema.load(json_data)

        title = data.get('title')
        description = data.get('description', '')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        location = data.get('location')
        is_recurring = data.get('is_recurring', False)

        if not title or not start_time or not end_time:
            return jsonify({'error': 'Missing required fields: title, start_time, end_time'}), 400

        event = Event(
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            creator_id=user_id_int,
            location=location,
            is_recurring=is_recurring
        )

        if event.is_recurring and 'recurrence_pattern' in data:
            recurrence_data = data['recurrence_pattern']
            pattern = RecurrencePattern(
                type=RecurrenceType(recurrence_data['type']),
                interval=recurrence_data.get('interval', 1),
                days_of_week=recurrence_data.get('days_of_week'),
                day_of_month=recurrence_data.get('day_of_month'),
                month_of_year=recurrence_data.get('month_of_year'),
                end_date=recurrence_data.get('end_date'),
                count=recurrence_data.get('count'),
                custom_rule=recurrence_data.get('custom_rule')
            )
            event.recurrence_pattern = pattern

        db.session.add(event)
        db.session.flush()

        permission = Permission(
            event_id=event.id,
            user_id=user_id_int,
            role=RoleType.OWNER,
            granted_by=user_id_int
        )
        db.session.add(permission)

        version = event.create_version(user_id_int)
        db.session.add(version)

        db.session.commit()

        return jsonify({
            'message': 'Event created successfully',
            'event': event.to_dict()
        }), 201

    except MarshmallowValidationError as e:
        return jsonify({'error': str(e)}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@events_bp.route('', methods=['GET'])
@jwt_required()
def get_events():
    """List all events the user has access to with pagination and filtering."""
    try:
        user_id = get_jwt_identity()

        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        search = request.args.get('search')

        query = Event.query.join(Permission).filter(
            Permission.user_id == user_id
        )

        if start_date:
            try:
                start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.filter(Event.end_time >= start)
            except ValueError:
                return jsonify({'error': 'Invalid start_date format'}), 400

        if end_date:
            try:
                end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.filter(Event.start_time <= end)
            except ValueError:
                return jsonify({'error': 'Invalid end_date format'}), 400

        if search:
            query = query.filter(Event.title.ilike(f'%{search}%'))

        paginated_events = query.paginate(page=page, per_page=per_page, error_out=False)

        events = [event.to_dict() for event in paginated_events.items]

        return jsonify({
            'events': events,
            'total': paginated_events.total,
            'pages': paginated_events.pages,
            'page': page,
            'per_page': per_page
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@events_bp.route('/<int:id>', methods=['GET'])
@jwt_required_with_role(['owner', 'editor', 'viewer'])
def get_event(id, permission=None):
    """Get a specific event by ID."""
    try:
        event = Event.query.get(id)

        if not event:
            return jsonify({'error': 'Event not found'}), 404

        return jsonify(event.to_dict()), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@events_bp.route('/<int:id>', methods=['PUT'])
@editor_required
def update_event(id, permission=None):
    """Update an event by ID."""
    try:
        user_id = get_jwt_identity()
        event = Event.query.get(id)

        if not event:
            return jsonify({'error': 'Event not found'}), 404

        schema = EventSchema()
        data = schema.load(request.get_json())

        version = event.create_version(user_id)
        db.session.add(version)

        event.title = data.get('title', event.title)
        event.description = data.get('description', event.description)
        event.start_time = data.get('start_time', event.start_time)
        event.end_time = data.get('end_time', event.end_time)
        event.location = data.get('location', event.location)
        event.is_recurring = data.get('is_recurring', event.is_recurring)

        if event.is_recurring and 'recurrence_pattern' in data:
            recurrence_data = data['recurrence_pattern']

            if not event.recurrence_pattern:
                pattern = RecurrencePattern(
                    type=RecurrenceType(recurrence_data['type']),
                    interval=recurrence_data.get('interval', 1),
                    days_of_week=recurrence_data.get('days_of_week'),
                    day_of_month=recurrence_data.get('day_of_month'),
                    month_of_year=recurrence_data.get('month_of_year'),
                    end_date=recurrence_data.get('end_date'),
                    count=recurrence_data.get('count'),
                    custom_rule=recurrence_data.get('custom_rule')
                )
                event.recurrence_pattern = pattern
            else:
                event.recurrence_pattern.type = RecurrenceType(recurrence_data.get('type', event.recurrence_pattern.type.value))
                event.recurrence_pattern.interval = recurrence_data.get('interval', event.recurrence_pattern.interval)
                event.recurrence_pattern.days_of_week = recurrence_data.get('days_of_week', event.recurrence_pattern.days_of_week)
                event.recurrence_pattern.day_of_month = recurrence_data.get('day_of_month', event.recurrence_pattern.day_of_month)
                event.recurrence_pattern.month_of_year = recurrence_data.get('month_of_year', event.recurrence_pattern.month_of_year)
                event.recurrence_pattern.end_date = recurrence_data.get('end_date', event.recurrence_pattern.end_date)
                event.recurrence_pattern.count = recurrence_data.get('count', event.recurrence_pattern.count)
                event.recurrence_pattern.custom_rule = recurrence_data.get('custom_rule', event.recurrence_pattern.custom_rule)

        if not event.is_recurring and event.recurrence_pattern:
            db.session.delete(event.recurrence_pattern)
            event.recurrence_pattern = None

        db.session.commit()

        return jsonify({
            'message': 'Event updated successfully',
            'event': event.to_dict()
        }), 200

    except MarshmallowValidationError as e:
        return jsonify({'error': str(e)}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@events_bp.route('/<int:id>', methods=['DELETE'])
@owner_required
def delete_event(id, permission=None):
    """Delete an event by ID."""
    try:
        event = Event.query.get(id)

        if not event:
            return jsonify({'error': 'Event not found'}), 404

        db.session.delete(event)
        db.session.commit()

        return jsonify({'message': 'Event deleted successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@events_bp.route('/batch', methods=['POST'])
@jwt_required()
def batch_create_events():
    """Create multiple events in a single request."""
    try:
        user_id = get_jwt_identity()

        user_id_int = int(user_id) if isinstance(user_id, str) else user_id

        json_data = request.get_json()
        if not json_data:
            return jsonify({'error': 'No JSON data provided'}), 400

        schema = BatchEventSchema()
        data = schema.load(json_data)

        if not 'events' in data or not data['events']:
            return jsonify({'error': 'No events provided in the request'}), 400

        created_events = []

        for event_data in data['events']:
            title = event_data.get('title')
            description = event_data.get('description', '')
            start_time = event_data.get('start_time')
            end_time = event_data.get('end_time')
            location = event_data.get('location')
            is_recurring = event_data.get('is_recurring', False)

            if not title or not start_time or not end_time:
                continue

            event = Event(
                title=title,
                description=description,
                start_time=start_time,
                end_time=end_time,
                creator_id=user_id_int,
                location=location,
                is_recurring=is_recurring
            )

            if event.is_recurring and 'recurrence_pattern' in event_data:
                recurrence_data = event_data['recurrence_pattern']
                pattern = RecurrencePattern(
                    type=RecurrenceType(recurrence_data['type']),
                    interval=recurrence_data.get('interval', 1),
                    days_of_week=recurrence_data.get('days_of_week'),
                    day_of_month=recurrence_data.get('day_of_month'),
                    month_of_year=recurrence_data.get('month_of_year'),
                    end_date=recurrence_data.get('end_date'),
                    count=recurrence_data.get('count'),
                    custom_rule=recurrence_data.get('custom_rule')
                )
                event.recurrence_pattern = pattern

            db.session.add(event)
            db.session.flush()

            permission = Permission(
                event_id=event.id,
                user_id=user_id_int,
                role=RoleType.OWNER,
                granted_by=user_id_int
            )
            db.session.add(permission)

            version = event.create_version(user_id_int)
            db.session.add(version)

            created_events.append(event)

        if not created_events:
            return jsonify({'error': 'No valid events to create'}), 400

        db.session.commit()

        return jsonify({
            'message': f'{len(created_events)} events created successfully',
            'events': [event.to_dict() for event in created_events]
        }), 201

    except MarshmallowValidationError as e:
        return jsonify({'error': str(e)}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500