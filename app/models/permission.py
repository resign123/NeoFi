from app import db
from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

class RoleType(PyEnum):
    OWNER = 'owner'
    EDITOR = 'editor'
    VIEWER = 'viewer'

class Permission(db.Model):
    __tablename__ = 'permissions'
    
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    role = Column(Enum(RoleType), nullable=False, default=RoleType.VIEWER)
    granted_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User', foreign_keys=[user_id])
    granter = relationship('User', foreign_keys=[granted_by])
    
    def __init__(self, event_id, user_id, role, granted_by):
        self.event_id = event_id
        self.user_id = user_id
        self.role = role
        self.granted_by = granted_by
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'user_id': self.user_id,
            'user': self.user.username if self.user else None,
            'role': self.role.value,
            'granted_by': self.granted_by,
            'granter': self.granter.username if self.granter else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def can_edit(self):
        return self.role in (RoleType.OWNER, RoleType.EDITOR)
    
    def can_view(self):
        return True  # All roles can view
    
    def can_delete(self):
        return self.role == RoleType.OWNER
    
    def can_share(self):
        return self.role == RoleType.OWNER
    
    def __repr__(self):
        return f'<Permission {self.user_id} {self.role.value} on {self.event_id}>' 