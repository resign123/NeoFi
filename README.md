# NeoFi Collaborative Event Management System

A RESTful API for an event scheduling application with collaborative editing features, allowing users to create, manage, and share events with role-based permissions and maintain a comprehensive history of changes.

## Features

- **Authentication and Authorization**
  - Secure JWT-based authentication system
  - Role-based access control (RBAC) with Owner, Editor, and Viewer roles

- **Event Management**
  - CRUD operations for events
  - Support for recurring events with customizable patterns
  - Conflict detection for overlapping events
  - Batch operations for creating multiple events

- **Collaboration Features**
  - Sharing system with granular permissions
  - Tracking edit history with attribution

- **Advanced Features**
  - Versioning system with rollback capability
  - Changelog with diff visualization
  - Transaction system for atomic operations

## Technology Stack

- Python 3.8+
- Flask framework
- SQLAlchemy ORM
- JWT for authentication
- SQLite (configurable to other databases)

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-username/neofi-event-management.git
   cd neofi-event-management
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory with the following variables:
   ```
   SECRET_KEY=your_secret_key_here
   JWT_SECRET_KEY=your_jwt_secret_key_here
   DATABASE_URI=sqlite:///neofi.db
   DEBUG=True
   HOST=127.0.0.1
   PORT=5000
   ```

5. Run the application:
   ```
   python run.py
   ```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login and receive an authentication token
- `POST /api/auth/refresh` - Refresh an authentication token
- `POST /api/auth/logout` - Invalidate the current token

### Event Management
- `POST /api/events` - Create a new event
- `GET /api/events` - List all events the user has access to with pagination and filtering
- `GET /api/events/{id}` - Get a specific event by ID
- `PUT /api/events/{id}` - Update an event by ID
- `DELETE /api/events/{id}` - Delete an event by ID
- `POST /api/events/batch` - Create multiple events in a single request

### Collaboration
- `POST /api/events/{id}/share` - Share an event with other users
- `GET /api/events/{id}/permissions` - List all permissions for an event
- `PUT /api/events/{id}/permissions/{userId}` - Update permissions for a user
- `DELETE /api/events/{id}/permissions/{userId}` - Remove access for a user

### Version History
- `GET /api/events/{id}/history` - Get all versions of an event
- `GET /api/events/{id}/history/{versionId}` - Get a specific version of an event
- `POST /api/events/{id}/rollback/{versionId}` - Rollback to a previous version

### Changelog & Diff
- `GET /api/events/{id}/changelog` - Get a chronological log of all changes to an event
- `GET /api/events/{id}/compare?from={versionId1}&to={versionId2}` - Get a diff between two versions

## Data Models

### User
- id: Integer (PK)
- username: String (unique)
- email: String (unique)
- password_hash: String
- created_at: DateTime
- updated_at: DateTime
- is_active: Boolean

### Event
- id: Integer (PK)
- title: String
- description: Text
- start_time: DateTime
- end_time: DateTime
- location: String
- is_recurring: Boolean
- creator_id: Integer (FK)
- created_at: DateTime
- updated_at: DateTime
- current_version: Integer

### RecurrencePattern
- id: Integer (PK)
- event_id: Integer (FK)
- type: Enum (daily, weekly, monthly, yearly, custom)
- interval: Integer
- days_of_week: String
- day_of_month: Integer
- month_of_year: Integer
- end_date: DateTime
- count: Integer
- custom_rule: Text

### Permission
- id: Integer (PK)
- event_id: Integer (FK)
- user_id: Integer (FK)
- role: Enum (owner, editor, viewer)
- granted_by: Integer (FK)
- created_at: DateTime
- updated_at: DateTime

### EventVersion
- id: Integer (PK)
- event_id: Integer (FK)
- version_number: Integer
- data: Text (JSON)
- created_at: DateTime
- created_by: Integer (FK)

### ChangeLog
- id: Integer (PK)
- event_id: Integer (FK)
- from_version: Integer
- to_version: Integer
- diff_text: Text
- timestamp: DateTime
- user_id: Integer (FK)
