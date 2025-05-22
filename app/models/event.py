# -*- coding: utf-8 -*-
from app import db
from datetime import datetime
import json
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum


class RecurrenceType(PyEnum):
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    YEARLY = 'yearly'
    CUSTOM = 'custom'


class RecurrencePattern(db.Model):
    __tablename__ = 'recurrence_patterns'

    id = Column(Integer, primary_key=True)
    type = Column(Enum(RecurrenceType), nullable=False)
    interval = Column(Integer, default=1)
    days_of_week = Column(String(20), nullable=True)
    day_of_month = Column(Integer, nullable=True)
    month_of_year = Column(Integer, nullable=True)
    end_date = Column(DateTime, nullable=True)
    count = Column(Integer, nullable=True)
    custom_rule = Column(Text, nullable=True)

    event_id = Column(Integer, ForeignKey('events.id'))

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type.value,
            'interval': self.interval,
            'days_of_week': self.days_of_week,
            'day_of_month': self.day_of_month,
            'month_of_year': self.month_of_year,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'count': self.count,
            'custom_rule': self.custom_rule
        }

    def __repr__(self):
        return f'<RecurrencePattern {self.type.value}>'


class Event(db.Model):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    location = Column(String(255), nullable=True)
    is_recurring = Column(Boolean, default=False)

    creator_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    creator = relationship('User', backref='created_events')

    recurrence_pattern = relationship('RecurrencePattern', uselist=False, cascade='all, delete-orphan')

    permissions = relationship('Permission', backref='event', cascade='all, delete-orphan')

    versions = relationship('EventVersion', backref='event', cascade='all, delete-orphan')

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    current_version = Column(Integer, default=1)

    def __init__(self, title, description, start_time, end_time, creator_id, location=None, is_recurring=False):
        self.title = title
        self.description = description
        self.start_time = start_time
        self.end_time = end_time
        self.creator_id = creator_id
        self.location = location
        self.is_recurring = is_recurring

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'location': self.location,
            'is_recurring': self.is_recurring,
            'creator_id': self.creator_id,
            'recurrence_pattern': self.recurrence_pattern.to_dict() if self.recurrence_pattern else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'current_version': self.current_version
        }
    
    def create_version(self, user_id):
        """Create a new version of this event"""
        from app.models.version import EventVersion
        
        # Increment version number
        self.current_version += 1
        
        # Create version record
        version_data = {
            'title': self.title,
            'description': self.description,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'location': self.location,
            'is_recurring': self.is_recurring
        }
        
        if self.recurrence_pattern:
            version_data['recurrence_pattern'] = {
                'type': self.recurrence_pattern.type.value,
                'interval': self.recurrence_pattern.interval,
                'days_of_week': self.recurrence_pattern.days_of_week,
                'day_of_month': self.recurrence_pattern.day_of_month,
                'month_of_year': self.recurrence_pattern.month_of_year,
                'end_date': self.recurrence_pattern.end_date.isoformat() if self.recurrence_pattern.end_date else None,
                'count': self.recurrence_pattern.count,
                'custom_rule': self.recurrence_pattern.custom_rule
            }
        
        version = EventVersion(
            event_id=self.id,
            version_number=self.current_version,
            created_by=user_id,
            data=json.dumps(version_data)
        )
        
        return version
    
    def __repr__(self):
        return f'<Event {self.title}>'