# Test Backend API

A FastAPI backend for the GlyphQA test application with JWT authentication and MongoDB integration.

## Features

- **JWT Authentication**: Secure login with token-based authentication
- **User Management**: Create and manage users with roles
- **MongoDB Integration**: Persistent data storage
- **CORS Support**: Configured for React frontend
- **Test Users**: Pre-configured admin and user accounts

## API Endpoints

### Authentication
- `POST /auth/login` - Login with username/password
- `GET /users/me` - Get current user info (requires auth)

### User Management
- `POST /users` - Create new user (requires admin auth)
- `GET /users` - List all users (requires admin auth)

### Health Check
- `GET /health` - API health status

## Test Users

The following users are automatically created on startup:

- **Admin User**:
  - Username: `admin`
  - Password: `admin_password`
  - Role: `admin`

- **Regular User**:
  - Username: `user`
  - Password: `password`
  - Role: `user`

## Environment Variables

Create a `.env` file with:

```env
SECRET_KEY=your-secret-key-here
MONGODB_URL=mongodb://localhost:27017/
```

## Running Locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start MongoDB (or use Docker):
   ```bash
   docker run -d -p 27017:27017 mongo:7.0
   ```

3. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

The API will be available at `http://localhost:8000`

## Docker

Build and run with Docker:

```bash
docker build -t test-backend .
docker run -p 8000:8000 test-backend
```

## Docker Compose

Use the provided `docker-compose.yml` in the parent directory to run the complete stack (frontend + backend + MongoDB).
