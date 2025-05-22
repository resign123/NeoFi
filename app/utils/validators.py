# -*- coding: utf-8 -*-
from datetime import datetime
from app.utils.errors import ValidationError
import re
from marshmallow import Schema, fields, validate, ValidationError as MarshmallowValidationError


class UserSchema(Schema):
    """Schema for user data validation."""
    username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8))


class LoginSchema(Schema):
    """Schema for login data validation."""
    username = fields.Str(required=False)
    email = fields.Email(required=False)
    password = fields.Str(required=True)
    
    def validate_login(self, data):
        """Validate that either username or email is provided."""
        if not data.get('username') and not data.get('email'):
            raise MarshmallowValidationError("Either username or email must be provided")
        return data


class RecurrencePatternSchema(Schema):
    """Schema for recurrence pattern validation."""
    type = fields.Str(required=True, validate=validate.OneOf(['daily', 'weekly', 'monthly', 'yearly', 'custom']))
    interval = fields.Int(required=False, default=1, validate=validate.Range(min=1, max=365))
    days_of_week = fields.Str(required=False)
    day_of_month = fields.Int(required=False, validate=validate.Range(min=1, max=31))
    month_of_year = fields.Int(required=False, validate=validate.Range(min=1, max=12))
    end_date = fields.DateTime(required=False)
    count = fields.Int(required=False, validate=validate.Range(min=1))
    custom_rule = fields.Str(required=False)


class EventSchema(Schema):
    """Schema for event data validation."""
    title = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    description = fields.Str(required=False)
    start_time = fields.DateTime(required=True)
    end_time = fields.DateTime(required=True)
    location = fields.Str(required=False)
    is_recurring = fields.Bool(required=False, default=False)
    recurrence_pattern = fields.Nested(RecurrencePatternSchema, required=False)
    
    def validate_event(self, data):
        """Validate event data."""
        
        if data.get('start_time') and data.get('end_time'):
            if data['start_time'] >= data['end_time']:
                raise MarshmallowValidationError("End time must be after start time")
        
        if data.get('is_recurring') and not data.get('recurrence_pattern'):
            raise MarshmallowValidationError("Recurrence pattern is required for recurring events")
        
        return data


class PermissionSchema(Schema):
    """Schema for permission data validation."""
    user_id = fields.Int(required=True)
    role = fields.Str(required=True, validate=validate.OneOf(['owner', 'editor', 'viewer']))


class BatchEventSchema(Schema):
    """Schema for batch event creation."""
    events = fields.List(fields.Nested(EventSchema), required=True, validate=validate.Length(min=1))


def validate_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValidationError("Invalid email format")
    return email


def validate_password(password):
    """Validate password strength."""
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long")
    
    if not (any(c.isupper() for c in password) and
            any(c.islower() for c in password) and
            any(c.isdigit() for c in password)):
        raise ValidationError("Password must contain at least one uppercase letter, one lowercase letter, and one digit")
    
    return password


def validate_date_range(start_time, end_time):
    """Validate that start_time is before end_time."""
    start = datetime.fromisoformat(start_time.replace('Z', '+00:00')) if isinstance(start_time, str) else start_time
    end = datetime.fromisoformat(end_time.replace('Z', '+00:00')) if isinstance(end_time, str) else end_time
    
    if start >= end:
        raise ValidationError("End time must be after start time")
    
    return start, end


def validate_recurrence(recurrence_data):
    """Validate recurrence pattern."""
    if not recurrence_data.get('type'):
        raise ValidationError("Recurrence type is required")
    
    rec_type = recurrence_data['type']
    
    if rec_type == 'weekly' and not recurrence_data.get('days_of_week'):
        raise ValidationError("Days of week are required for weekly recurrence")
    
    if rec_type == 'monthly' and not recurrence_data.get('day_of_month'):
        raise ValidationError("Day of month is required for monthly recurrence")
    
    if rec_type == 'yearly' and (not recurrence_data.get('month_of_year') or not recurrence_data.get('day_of_month')):
        raise ValidationError("Month and day are required for yearly recurrence")
    
    if not recurrence_data.get('end_date') and not recurrence_data.get('count'):
        raise ValidationError("Either end date or count is required for recurrence")
    
    return recurrence_data