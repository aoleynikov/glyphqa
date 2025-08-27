from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Test Backend API")

# CORS middleware - more permissive for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "test-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing - using sha256_crypt instead of bcrypt
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

# JWT token security
security = HTTPBearer()

# MongoDB connection
client = MongoClient(os.getenv("MONGODB_URL", "mongodb://localhost:27017/"))
db = client.test_app
users_collection = db.users

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "user"

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token_data = TokenData(username=username)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data

def get_current_user(token_data: TokenData = Depends(verify_token)):
    user = users_collection.find_one({"username": token_data.username})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# Initialize test users
def init_test_users():
    test_users = [
        {
            "username": "admin",
            "email": "admin@example.com",
            "password": get_password_hash("admin_password"),
            "role": "admin"
        },
        {
            "username": "user",
            "email": "user@example.com", 
            "password": get_password_hash("password"),
            "role": "user"
        }
    ]
    
    for user_data in test_users:
        try:
            users_collection.insert_one(user_data)
            print(f"Created test user: {user_data['username']}")
        except DuplicateKeyError:
            print(f"Test user already exists: {user_data['username']}")

# Startup event
@app.on_event("startup")
async def startup_event():
    # Create unique index on username
    users_collection.create_index("username", unique=True)
    # Initialize test users
    init_test_users()

# Routes
@app.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    user = users_collection.find_one({"username": user_credentials.username})
    if not user or not verify_password(user_credentials.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate):
    try:
        user_data = user.dict()
        user_data["password"] = get_password_hash(user_data["password"])
        
        result = users_collection.insert_one(user_data)
        user_data["id"] = str(result.inserted_id)
        
        # Remove password from response
        del user_data["password"]
        return UserResponse(**user_data)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

@app.get("/users/me", response_model=UserResponse)
async def get_current_user_info(current_user = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user["_id"]),
        username=current_user["username"],
        email=current_user["email"],
        role=current_user["role"]
    )

@app.get("/users", response_model=list[UserResponse])
async def get_users(current_user = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    users = []
    for user in users_collection.find({}, {"password": 0}):
        user["id"] = str(user["_id"])
        users.append(UserResponse(**user))
    return users

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
