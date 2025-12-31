from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
from jose import JWTError, jwt
import io
import csv
from ofxparse import OfxParser
from decimal import Decimal

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production-please-make-it-secure')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    is_admin: bool = False
    is_approved: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class FamilyMember(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    profile: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FamilyMemberCreate(BaseModel):
    name: str
    profile: Optional[str] = None

class Bank(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BankCreate(BaseModel):
    name: str
    active: bool = True

class Category(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CategoryCreate(BaseModel):
    name: str
    type: str

class Transaction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: datetime
    description: str
    amount: float
    type: str
    category_id: Optional[str] = None
    member_id: str
    bank_id: str
    is_reserve_deposit: bool = False
    is_reserve_withdrawal: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TransactionCreate(BaseModel):
    date: datetime
    description: str
    amount: float
    type: str
    category_id: Optional[str] = None
    member_id: str
    bank_id: str
    is_reserve_deposit: bool = False
    is_reserve_withdrawal: bool = False

class Goal(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    target_amount: float
    current_amount: float = 0.0
    deadline: Optional[datetime] = None
    image_url: Optional[str] = None
    monthly_contribution: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GoalCreate(BaseModel):
    name: str
    description: Optional[str] = None
    target_amount: float
    deadline: Optional[datetime] = None
    image_url: Optional[str] = None
    monthly_contribution: float = 0.0

class GoalContribution(BaseModel):
    amount: float

class DashboardSummary(BaseModel):
    previous_balance: float
    month_income: float
    month_expenses: float
    final_balance: float

class CategoryChart(BaseModel):
    category: str
    amount: float
    percentage: float

class MonthlyComparison(BaseModel):
    month: str
    income: float
    expenses: float

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

@api_router.post("/auth/register")
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt())
    
    user_count = await db.users.count_documents({})
    is_first_user = user_count == 0
    
    user = User(
        email=user_data.email, 
        name=user_data.name,
        is_admin=is_first_user,
        is_approved=is_first_user
    )
    user_dict = user.model_dump()
    user_dict['timestamp'] = user_dict['created_at'].isoformat()
    del user_dict['created_at']
    user_dict['password'] = hashed_password.decode('utf-8')
    
    await db.users.insert_one(user_dict)
    
    if not is_first_user:
        raise HTTPException(status_code=202, detail="Conta criada! Aguarde aprovação do administrador.")
    
    access_token_expires = timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    access_token = jwt.encode(
        {"sub": user.id, "exp": datetime.now(timezone.utc) + access_token_expires},
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    
    fixed_categories = [
        {"name": "Reserva de Emergência", "type": "especial"},
        {"name": "Alimentação", "type": "despesa"},
        {"name": "Transporte", "type": "despesa"},
        {"name": "Saúde", "type": "despesa"},
        {"name": "Lazer", "type": "despesa"},
        {"name": "Educação", "type": "despesa"},
        {"name": "Moradia", "type": "despesa"},
        {"name": "Salário", "type": "receita"},
        {"name": "Freelance", "type": "receita"},
    ]
    
    for cat_data in fixed_categories:
        cat = Category(name=cat_data["name"], type=cat_data["type"])
        cat_dict = cat.model_dump()
        cat_dict['created_at'] = cat_dict['created_at'].isoformat()
        cat_dict['user_id'] = user.id
        cat_dict['is_fixed'] = True
        await db.categories.insert_one(cat_dict)
    
    return Token(access_token=access_token, token_type="bearer", user=user)

@api_router.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    user_doc = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not bcrypt.checkpw(user_data.password.encode('utf-8'), user_doc['password'].encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not user_doc.get('is_approved', False):
        raise HTTPException(status_code=403, detail="Conta ainda não aprovada pelo administrador")
    
    user = User(
        id=user_doc['id'],
        email=user_doc['email'],
        name=user_doc['name'],
        is_admin=user_doc.get('is_admin', False),
        is_approved=user_doc.get('is_approved', False),
        created_at=datetime.fromisoformat(user_doc['timestamp']) if isinstance(user_doc.get('timestamp'), str) else user_doc.get('created_at')
    )
    
    access_token_expires = timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    access_token = jwt.encode(
        {"sub": user.id, "exp": datetime.now(timezone.utc) + access_token_expires},
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    
    return Token(access_token=access_token, token_type="bearer", user=user)

async def verify_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    user_id = await verify_token(credentials)
    user_doc = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user_doc or not user_doc.get('is_admin', False):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id

@api_router.get("/admin/users")
async def get_all_users(user_id: str = Depends(verify_admin)):
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    return users

@api_router.post("/admin/users/{user_email}/approve")
async def approve_user(user_email: str, admin_id: str = Depends(verify_admin)):
    result = await db.users.update_one(
        {"email": user_email},
        {"$set": {"is_approved": True}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User approved successfully"}

@api_router.delete("/admin/users/{user_email}")
async def delete_user(user_email: str, admin_id: str = Depends(verify_admin)):
    result = await db.users.delete_one({"email": user_email})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

class PasswordReset(BaseModel):
    new_password: str

@api_router.post("/admin/users/{user_email}/reset-password")
async def reset_user_password(user_email: str, data: PasswordReset, admin_id: str = Depends(verify_admin)):
    hashed_password = bcrypt.hashpw(data.new_password.encode('utf-8'), bcrypt.gensalt())
    
    result = await db.users.update_one(
        {"email": user_email},
        {"$set": {"password": hashed_password.decode('utf-8')}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": f"Password reset successfully for {user_email}"}

# Goals endpoints
@api_router.post("/goals", response_model=Goal)
async def create_goal(goal: GoalCreate, user_id: str = Depends(verify_token)):
    goal_obj = Goal(**goal.model_dump())
    doc = goal_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    if doc.get('deadline'):
        doc['deadline'] = doc['deadline'].isoformat()
    doc['user_id'] = user_id
    await db.goals.insert_one(doc)
    return goal_obj

@api_router.get("/goals", response_model=List[Goal])
async def get_goals(user_id: str = Depends(verify_token)):
    goals = await db.goals.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    for goal in goals:
        if isinstance(goal['created_at'], str):
            goal['created_at'] = datetime.fromisoformat(goal['created_at'])
        if goal.get('deadline') and isinstance(goal['deadline'], str):
            goal['deadline'] = datetime.fromisoformat(goal['deadline'])
    return goals

@api_router.put("/goals/{goal_id}", response_model=Goal)
async def update_goal(goal_id: str, goal: GoalCreate, user_id: str = Depends(verify_token)):
    update_data = goal.model_dump()
    if update_data.get('deadline'):
        update_data['deadline'] = update_data['deadline'].isoformat()
    
    result = await db.goals.update_one(
        {"id": goal_id, "user_id": user_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    updated = await db.goals.find_one({"id": goal_id}, {"_id": 0})
    if isinstance(updated['created_at'], str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    if updated.get('deadline') and isinstance(updated['deadline'], str):
        updated['deadline'] = datetime.fromisoformat(updated['deadline'])
    
    return Goal(**updated)

@api_router.post("/goals/{goal_id}/contribute")
async def add_goal_contribution(goal_id: str, contribution: GoalContribution, user_id: str = Depends(verify_token)):
    result = await db.goals.update_one(
        {"id": goal_id, "user_id": user_id},
        {"$inc": {"current_amount": contribution.amount}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    updated = await db.goals.find_one({"id": goal_id}, {"_id": 0})
    if isinstance(updated['created_at'], str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    if updated.get('deadline') and isinstance(updated['deadline'], str):
        updated['deadline'] = datetime.fromisoformat(updated['deadline'])
    
    return Goal(**updated)

@api_router.delete("/goals/{goal_id}")
async def delete_goal(goal_id: str, user_id: str = Depends(verify_token)):
    result = await db.goals.delete_one({"id": goal_id, "user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"message": "Goal deleted successfully"}

# Continue with remaining endpoints...
# [REST OF CODE CONTINUES - Character limit reached, continuing in next file]