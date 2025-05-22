from app import db
from datetime import datetime
import json
import difflib
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

class EventVersion(db.Model):
    __tablename__ = 'event_versions'
    
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False)
    version_number = Column(Integer, nullable=False)
    data = Column(Text, nullable=False)  # JSON string of event data
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationship
    author = relationship('User', foreign_keys=[created_by])
    
    def __init__(self, event_id, version_number, data, created_by):
        self.event_id = event_id
        self.version_number = version_number
        self.data = data
        self.created_by = created_by
    
    def get_data_dict(self):
        return json.loads(self.data)
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'version_number': self.version_number,
            'data': self.get_data_dict(),
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by,
            'author': self.author.username if self.author else None
        }
    
    def diff_with(self, other_version):
        """Generate a diff between this version and another version."""
        this_data = json.dumps(self.get_data_dict(), indent=4).splitlines()
        other_data = json.dumps(other_version.get_data_dict(), indent=4).splitlines()
        
        differ = difflib.Differ()
        diff = list(differ.compare(other_data, this_data))
        
        # Create changelog entry
        return ChangeLog(
            event_id=self.event_id,
            from_version=other_version.version_number,
            to_version=self.version_number,
            diff_text='\n'.join(diff),
            user_id=self.created_by
        )
    
    def __repr__(self):
        return f'<EventVersion {self.event_id} v{self.version_number}>'

class ChangeLog(db.Model):
    __tablename__ = 'changelog'
    
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False)
    from_version = Column(Integer, nullable=False)
    to_version = Column(Integer, nullable=False)
    diff_text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    event = relationship('Event')
    user = relationship('User')
    
    def __init__(self, event_id, from_version, to_version, diff_text, user_id):
        self.event_id = event_id
        self.from_version = from_version
        self.to_version = to_version
        self.diff_text = diff_text
        self.user_id = user_id
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'from_version': self.from_version,
            'to_version': self.to_version,
            'diff_text': self.diff_text,
            'timestamp': self.timestamp.isoformat(),
            'user_id': self.user_id,
            'user': self.user.username if self.user else None
        }
    
    def get_html_diff(self):
        """Convert the diff text to HTML format for better visualization."""
        lines = self.diff_text.splitlines()
        html = []
        
        for line in lines:
            if line.startswith('+'):
                html.append(f'<div class="addition">{line}</div>')
            elif line.startswith('-'):
                html.append(f'<div class="deletion">{line}</div>')
            elif line.startswith('?'):
                html.append(f'<div class="info">{line}</div>')
            else:
                html.append(f'<div class="unchanged">{line}</div>')
        
        return '\n'.join(html)
    
    def __repr__(self):
        return f'<ChangeLog {self.event_id} {self.from_version}->{self.to_version}>' 