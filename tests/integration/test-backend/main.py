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
tickets_collection = db.tickets

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

class TicketCreate(BaseModel):
    content: str

class TicketResponse(BaseModel):
    id: str
    content: str
    status: str
    submitter: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    submitted_at: datetime
    created_at: datetime

class TicketResolve(BaseModel):
    action: str

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

def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))):
    if credentials is None:
        return None
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        user = users_collection.find_one({"username": username})
        return user
    except JWTError:
        return None

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

    # Create unique indexes on username and email
    users_collection.create_index("username", unique=True)
    users_collection.create_index("email", unique=True)
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
    except DuplicateKeyError as e:
        # Check which field caused the duplicate key error
        error_message = str(e)
        if "username" in error_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        elif "email" in error_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this information already exists"
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

@app.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Check if user exists
    from bson import ObjectId
    try:
        user_object_id = ObjectId(user_id)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    user_to_delete = users_collection.find_one({"_id": user_object_id})
    if not user_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent admin from deleting themselves
    if user_to_delete["username"] == current_user["username"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Delete the user
    result = users_collection.delete_one({"_id": user_object_id})
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User deleted successfully"}

@app.post("/tickets", response_model=TicketResponse)
async def create_ticket(ticket: TicketCreate, current_user = Depends(get_optional_user)):
    now = datetime.utcnow()
    ticket_data = {
        "content": ticket.content,
        "status": "ToDo",
        "submitter": current_user["username"] if current_user else None,
        "resolved_by": None,
        "resolved_at": None,
        "submitted_at": now,
        "created_at": now
    }
    
    result = tickets_collection.insert_one(ticket_data)
    ticket_data["id"] = str(result.inserted_id)
    
    return TicketResponse(**ticket_data)

@app.get("/tickets", response_model=list[TicketResponse])
async def get_tickets(current_user = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    tickets = []
    for ticket in tickets_collection.find({}):
        ticket["id"] = str(ticket["_id"])
        tickets.append(TicketResponse(**ticket))
    return tickets

@app.get("/tickets/todo", response_model=TicketResponse)
async def get_todo_ticket(current_user = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    todo_ticket = tickets_collection.find_one(
        {"status": "ToDo"},
        sort=[("submitted_at", 1)]
    )
    
    if not todo_ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No todo tickets available"
        )
    
    todo_ticket["id"] = str(todo_ticket["_id"])
    return TicketResponse(**todo_ticket)

@app.patch("/tickets/{ticket_id}/resolve", response_model=TicketResponse)
async def resolve_ticket(ticket_id: str, resolve_action: TicketResolve, current_user = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    if resolve_action.action not in ["accept", "reject"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Action must be 'accept' or 'reject'"
        )
    
    from bson import ObjectId
    try:
        ticket_object_id = ObjectId(ticket_id)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ticket ID format"
        )
    
    ticket = tickets_collection.find_one({"_id": ticket_object_id})
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    status_value = "Accepted" if resolve_action.action == "accept" else "Rejected"
    now = datetime.utcnow()
    
    tickets_collection.update_one(
        {"_id": ticket_object_id},
        {
            "$set": {
                "status": status_value,
                "resolved_by": current_user["username"],
                "resolved_at": now
            }
        }
    )
    
    updated_ticket = tickets_collection.find_one({"_id": ticket_object_id})
    updated_ticket["id"] = str(updated_ticket["_id"])
    return TicketResponse(**updated_ticket)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
