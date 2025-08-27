# Integration Test Environment

This directory contains a complete test environment for GlyphQA with a React frontend and FastAPI backend.

## Architecture

- **Frontend**: React.js application with Bootstrap UI
- **Backend**: FastAPI with JWT authentication
- **Database**: MongoDB for data persistence
- **Containerization**: Docker Compose for easy deployment

## Quick Start

### Using Docker Compose (Recommended)

1. Start the complete stack:
   ```bash
   docker-compose up -d
   ```

2. Access the applications:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

3. Stop the stack:
   ```bash
   docker-compose down
   ```

### Manual Setup

#### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd test-backend
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start MongoDB:
   ```bash
   docker run -d -p 27017:27017 mongo:7.0
   ```

4. Run the backend:
   ```bash
   uvicorn main:app --reload
   ```

#### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd test-web-app
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

## Test Users

The backend automatically creates these test users on startup:

- **Admin**: `admin` / `admin_password`
- **User**: `user` / `password`

## API Endpoints

### Authentication
- `POST /auth/login` - Login
- `GET /users/me` - Get current user

### User Management
- `POST /users` - Create user (admin only)
- `GET /users` - List users (admin only)

## Features

### Frontend
- Role-based navigation (admin vs user)
- User management interface
- JWT token handling
- Responsive Bootstrap UI

### Backend
- JWT authentication
- MongoDB integration
- User role management
- CORS configuration
- Automatic test user creation

## Development

### Backend Development
- FastAPI with automatic API documentation
- Hot reload enabled in development
- Environment variable configuration
- Comprehensive error handling

### Frontend Development
- React with functional components
- Bootstrap for styling
- Environment variable support
- Token-based authentication

## Testing with GlyphQA

This environment is designed to work with the GlyphQA framework:

1. Update `glyph.config.yml` to point to the correct URLs
2. Create scenarios that test the login flow and user management
3. Use the provided test users for authentication scenarios

## Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 3000, 8000, and 27017 are available
2. **MongoDB connection**: Check if MongoDB is running and accessible
3. **CORS errors**: Verify the frontend URL is allowed in backend CORS settings
4. **Token expiration**: JWT tokens expire after 30 minutes by default

### Logs

View logs for individual services:
```bash
docker-compose logs frontend
docker-compose logs backend
docker-compose logs mongodb
```
