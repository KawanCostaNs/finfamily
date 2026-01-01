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

# Family endpoints
@api_router.post("/family", response_model=FamilyMember)
async def create_family_member(member: FamilyMemberCreate, user_id: str = Depends(verify_token)):
    member_obj = FamilyMember(**member.model_dump())
    doc = member_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['user_id'] = user_id
    await db.family_members.insert_one(doc)
    return member_obj

@api_router.get("/family", response_model=List[FamilyMember])
async def get_family_members(user_id: str = Depends(verify_token)):
    members = await db.family_members.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    for member in members:
        if isinstance(member['created_at'], str):
            member['created_at'] = datetime.fromisoformat(member['created_at'])
    return members

@api_router.put("/family/{member_id}", response_model=FamilyMember)
async def update_family_member(member_id: str, member: FamilyMemberCreate, user_id: str = Depends(verify_token)):
    result = await db.family_members.update_one({"id": member_id, "user_id": user_id}, {"$set": member.model_dump()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Member not found")
    updated = await db.family_members.find_one({"id": member_id}, {"_id": 0})
    if isinstance(updated['created_at'], str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    return FamilyMember(**updated)

@api_router.delete("/family/{member_id}")
async def delete_family_member(member_id: str, user_id: str = Depends(verify_token)):
    result = await db.family_members.delete_one({"id": member_id, "user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Member not found")
    return {"message": "Member deleted successfully"}

# Banks endpoints
@api_router.post("/banks", response_model=Bank)
async def create_bank(bank: BankCreate, user_id: str = Depends(verify_token)):
    bank_obj = Bank(**bank.model_dump())
    doc = bank_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['user_id'] = user_id
    await db.banks.insert_one(doc)
    return bank_obj

@api_router.get("/banks", response_model=List[Bank])
async def get_banks(user_id: str = Depends(verify_token)):
    banks = await db.banks.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    for bank in banks:
        if isinstance(bank['created_at'], str):
            bank['created_at'] = datetime.fromisoformat(bank['created_at'])
    return banks

@api_router.put("/banks/{bank_id}", response_model=Bank)
async def update_bank(bank_id: str, bank: BankCreate, user_id: str = Depends(verify_token)):
    result = await db.banks.update_one({"id": bank_id, "user_id": user_id}, {"$set": bank.model_dump()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Bank not found")
    updated = await db.banks.find_one({"id": bank_id}, {"_id": 0})
    if isinstance(updated['created_at'], str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    return Bank(**updated)

@api_router.delete("/banks/{bank_id}")
async def delete_bank(bank_id: str, user_id: str = Depends(verify_token)):
    result = await db.banks.delete_one({"id": bank_id, "user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Bank not found")
    return {"message": "Bank deleted successfully"}

# Categories endpoints
@api_router.post("/categories", response_model=Category)
async def create_category(category: CategoryCreate, user_id: str = Depends(verify_token)):
    category_obj = Category(**category.model_dump())
    doc = category_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['user_id'] = user_id
    await db.categories.insert_one(doc)
    return category_obj

@api_router.get("/categories", response_model=List[Category])
async def get_categories(user_id: str = Depends(verify_token)):
    categories = await db.categories.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    for category in categories:
        if isinstance(category['created_at'], str):
            category['created_at'] = datetime.fromisoformat(category['created_at'])
    return categories

@api_router.put("/categories/{category_id}", response_model=Category)
async def update_category(category_id: str, category: CategoryCreate, user_id: str = Depends(verify_token)):
    result = await db.categories.update_one({"id": category_id, "user_id": user_id}, {"$set": category.model_dump()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    updated = await db.categories.find_one({"id": category_id}, {"_id": 0})
    if isinstance(updated['created_at'], str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    return Category(**updated)

@api_router.delete("/categories/{category_id}")
async def delete_category(category_id: str, user_id: str = Depends(verify_token)):
    result = await db.categories.delete_one({"id": category_id, "user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted successfully"}

# Continue on next message due to length...

# Transactions endpoints
@api_router.post("/transactions/import")
async def import_transactions(file: UploadFile = File(...), member_id: str = Form(...), bank_id: str = Form(...), user_id: str = Depends(verify_token)):
    content = await file.read()
    file_extension = file.filename.lower().split('.')[-1] if file.filename else ''
    transactions, duplicates_count = [], 0
    
    try:
        if file_extension == 'csv':
            csv_content = content.decode('utf-8')
            lines = csv_content.split('\n')
            data_start = 0
            for i, line in enumerate(lines):
                if 'Data' in line and ('Lançamento' in line or 'Lancamento' in line or 'Valor' in line):
                    data_start = i
                    break
            csv_data = '\n'.join(lines[data_start:])
            delimiter = ';' if ';' in csv_data.split('\n')[0] else ','
            csv_reader = csv.DictReader(io.StringIO(csv_data), delimiter=delimiter)
            
            for row in csv_reader:
                try:
                    date_str = (row.get('Data Lançamento') or row.get('Data Lancamento') or row.get('Data') or row.get('date') or row.get('Date') or row.get('DATA') or '').strip()
                    description = (row.get('Descrição') or row.get('Descricao') or row.get('Histórico') or row.get('Historico') or row.get('description') or row.get('Description') or row.get('DESCRICAO') or 'N/A').strip()
                    amount_str = (row.get('Valor') or row.get('amount') or row.get('Amount') or row.get('VALOR') or '0').strip()
                    
                    if not amount_str or amount_str == '0':
                        continue
                    
                    amount_str = amount_str.replace('R$', '').replace('$', '').replace(' ', '')
                    if ',' in amount_str:
                        parts = amount_str.rsplit(',', 1)
                        integer_part = parts[0].replace('.', '')
                        decimal_part = parts[1] if len(parts) > 1 else '00'
                        amount_str = f"{integer_part}.{decimal_part}"
                    
                    amount = float(amount_str)
                    trans_type = 'receita' if amount > 0 else 'despesa'
                    trans_date = datetime.now(timezone.utc)
                    
                    if date_str:
                        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
                            try:
                                trans_date = datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
                                break
                            except ValueError:
                                continue
                    
                    existing = await db.transactions.find_one({"user_id": user_id, "date": trans_date.isoformat(), "description": description, "amount": abs(amount), "member_id": member_id, "bank_id": bank_id})
                    if existing:
                        duplicates_count += 1
                        continue
                    
                    transaction = Transaction(date=trans_date, description=description, amount=abs(amount), type=trans_type, member_id=member_id, bank_id=bank_id)
                    transactions.append(transaction)
                except Exception as e:
                    logging.error(f"Error parsing CSV row: {e}")
                    continue
        
        elif file_extension == 'ofx':
            ofx = OfxParser.parse(io.BytesIO(content))
            for account in ofx.accounts:
                for trans in account.statement.transactions:
                    amount = float(trans.amount)
                    trans_type = 'receita' if amount > 0 else 'despesa'
                    trans_date = trans.date.replace(tzinfo=timezone.utc) if trans.date else datetime.now(timezone.utc)
                    description = trans.memo or trans.payee or 'N/A'
                    
                    existing = await db.transactions.find_one({"user_id": user_id, "date": trans_date.isoformat(), "description": description, "amount": abs(amount), "member_id": member_id, "bank_id": bank_id})
                    if existing:
                        duplicates_count += 1
                        continue
                    
                    transaction = Transaction(date=trans_date, description=description, amount=abs(amount), type=trans_type, member_id=member_id, bank_id=bank_id)
                    transactions.append(transaction)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        if transactions:
            docs = []
            for trans in transactions:
                doc = trans.model_dump()
                doc['date'] = doc['date'].isoformat()
                doc['created_at'] = doc['created_at'].isoformat()
                doc['user_id'] = user_id
                docs.append(doc)
            await db.transactions.insert_many(docs)
        
        message = f"Successfully imported {len(transactions)} new transactions"
        if duplicates_count > 0:
            message += f" ({duplicates_count} duplicates skipped)"
        
        return {"message": message, "count": len(transactions), "duplicates": duplicates_count, "total_processed": len(transactions) + duplicates_count}
    except Exception as e:
        logging.error(f"Error importing: {e}")
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")

@api_router.get("/transactions", response_model=List[Transaction])
async def get_transactions(month: Optional[int] = None, year: Optional[int] = None, user_id: str = Depends(verify_token)):
    query = {"user_id": user_id}
    transactions = await db.transactions.find(query, {"_id": 0}).to_list(10000)
    for trans in transactions:
        if isinstance(trans['date'], str):
            trans['date'] = datetime.fromisoformat(trans['date'])
        if isinstance(trans['created_at'], str):
            trans['created_at'] = datetime.fromisoformat(trans['created_at'])
    if month and year:
        transactions = [t for t in transactions if t['date'].month == month and t['date'].year == year]
    return sorted(transactions, key=lambda x: x['date'], reverse=True)

@api_router.get("/transactions/{transaction_id}", response_model=Transaction)
async def get_transaction(transaction_id: str, user_id: str = Depends(verify_token)):
    trans = await db.transactions.find_one({"id": transaction_id, "user_id": user_id}, {"_id": 0})
    if not trans:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if isinstance(trans['date'], str):
        trans['date'] = datetime.fromisoformat(trans['date'])
    if isinstance(trans['created_at'], str):
        trans['created_at'] = datetime.fromisoformat(trans['created_at'])
    return Transaction(**trans)

@api_router.put("/transactions/{transaction_id}", response_model=Transaction)
async def update_transaction(transaction_id: str, transaction: TransactionCreate, user_id: str = Depends(verify_token)):
    update_data = transaction.model_dump()
    update_data['date'] = update_data['date'].isoformat()
    result = await db.transactions.update_one({"id": transaction_id, "user_id": user_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")
    updated = await db.transactions.find_one({"id": transaction_id}, {"_id": 0})
    if isinstance(updated['date'], str):
        updated['date'] = datetime.fromisoformat(updated['date'])
    if isinstance(updated['created_at'], str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    return Transaction(**updated)

@api_router.delete("/transactions/{transaction_id}")
async def delete_transaction(transaction_id: str, user_id: str = Depends(verify_token)):
    result = await db.transactions.delete_one({"id": transaction_id, "user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"message": "Transaction deleted successfully"}

class BulkCategorizeRequest(BaseModel):
    transaction_ids: List[str]
    category_id: str

@api_router.post("/transactions/bulk-categorize")
async def bulk_categorize_transactions(data: BulkCategorizeRequest, user_id: str = Depends(verify_token)):
    result = await db.transactions.update_many({"id": {"$in": data.transaction_ids}, "user_id": user_id}, {"$set": {"category_id": data.category_id}})
    return {"message": f"Successfully categorized {result.modified_count} transactions", "count": result.modified_count}

@api_router.post("/transactions/{transaction_id}/mark-reserve")
async def mark_as_reserve(transaction_id: str, is_deposit: bool, user_id: str = Depends(verify_token)):
    result = await db.transactions.update_one({"id": transaction_id, "user_id": user_id}, {"$set": {"is_reserve_deposit": is_deposit if is_deposit else False, "is_reserve_withdrawal": not is_deposit if not is_deposit else False}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"message": "Transaction marked successfully"}

@api_router.get("/dashboard/emergency-reserve")
async def get_emergency_reserve(user_id: str = Depends(verify_token)):
    # Buscar a categoria "Reserva de Emergência"
    reserve_category = await db.categories.find_one({"user_id": user_id, "name": "Reserva de Emergência"}, {"_id": 0})
    reserve_category_id = reserve_category['id'] if reserve_category else None
    
    transactions = await db.transactions.find({"user_id": user_id}, {"_id": 0}).to_list(10000)
    
    total = 0
    for trans in transactions:
        # Método 1: Via flags is_reserve_deposit/is_reserve_withdrawal
        if trans.get('is_reserve_deposit'):
            total += trans['amount']
        elif trans.get('is_reserve_withdrawal'):
            total -= trans['amount']
        # Método 2: Via categoria "Reserva de Emergência"
        elif reserve_category_id and trans.get('category_id') == reserve_category_id:
            # Se é receita na categoria reserva, adiciona. Se é despesa, subtrai
            if trans.get('type') == 'receita':
                total += trans['amount']
            else:
                total -= trans['amount']
    
    return {"total": total}

@api_router.get("/dashboard/summary", response_model=DashboardSummary)
async def get_dashboard_summary(month: int, year: int, user_id: str = Depends(verify_token)):
    transactions = await db.transactions.find({"user_id": user_id}, {"_id": 0}).to_list(10000)
    for trans in transactions:
        if isinstance(trans['date'], str):
            trans['date'] = datetime.fromisoformat(trans['date'])
    current_month_trans = [t for t in transactions if t['date'].month == month and t['date'].year == year]
    previous_month = month - 1 if month > 1 else 12
    previous_year = year if month > 1 else year - 1
    previous_trans = [t for t in transactions if (t['date'].year < previous_year) or (t['date'].year == previous_year and t['date'].month < previous_month) or (t['date'].year == previous_year and t['date'].month == previous_month)]
    previous_balance = sum(t['amount'] if t['type'] == 'receita' else -t['amount'] for t in previous_trans)
    month_income = sum(t['amount'] for t in current_month_trans if t['type'] == 'receita')
    month_expenses = sum(t['amount'] for t in current_month_trans if t['type'] == 'despesa')
    return DashboardSummary(previous_balance=previous_balance, month_income=month_income, month_expenses=month_expenses, final_balance=previous_balance + month_income - month_expenses)

@api_router.get("/dashboard/category-chart", response_model=List[CategoryChart])
async def get_category_chart(month: int, year: int, user_id: str = Depends(verify_token)):
    transactions = await db.transactions.find({"user_id": user_id}, {"_id": 0}).to_list(10000)
    categories = await db.categories.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    category_map = {c['id']: c['name'] for c in categories}
    for trans in transactions:
        if isinstance(trans['date'], str):
            trans['date'] = datetime.fromisoformat(trans['date'])
    current_month_trans = [t for t in transactions if t['date'].month == month and t['date'].year == year and t['type'] == 'despesa']
    category_totals = {}
    for trans in current_month_trans:
        cat_id = trans.get('category_id')
        cat_name = category_map.get(cat_id, 'Sem Categoria') if cat_id else 'Sem Categoria'
        category_totals[cat_name] = category_totals.get(cat_name, 0) + trans['amount']
    total = sum(category_totals.values())
    result = [CategoryChart(category=cat, amount=amount, percentage=round((amount/total*100) if total > 0 else 0, 2)) for cat, amount in category_totals.items()]
    return sorted(result, key=lambda x: x.amount, reverse=True)

@api_router.get("/dashboard/monthly-comparison", response_model=List[MonthlyComparison])
async def get_monthly_comparison(year: int, user_id: str = Depends(verify_token)):
    transactions = await db.transactions.find({"user_id": user_id}, {"_id": 0}).to_list(10000)
    for trans in transactions:
        if isinstance(trans['date'], str):
            trans['date'] = datetime.fromisoformat(trans['date'])
    year_trans = [t for t in transactions if t['date'].year == year]
    month_names = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    result = []
    for month_num in range(1, 13):
        month_trans = [t for t in year_trans if t['date'].month == month_num]
        income = sum(t['amount'] for t in month_trans if t['type'] == 'receita')
        expenses = sum(t['amount'] for t in month_trans if t['type'] == 'despesa')
        result.append(MonthlyComparison(month=month_names[month_num-1], income=income, expenses=expenses))
    return result

# ==================== GAMIFICATION MODELS ====================

class Badge(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    icon: str  # emoji or icon name
    criteria: str  # how to earn this badge
    unlocked: bool = False
    unlocked_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FamilyChallenge(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    target_amount: float
    current_amount: float = 0.0
    reward: str  # what the family gets when completing
    deadline: Optional[datetime] = None
    category_id: Optional[str] = None  # optional category to track
    is_active: bool = True
    is_completed: bool = False
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FamilyChallengeCreate(BaseModel):
    name: str
    description: str
    target_amount: float
    reward: str
    deadline: Optional[datetime] = None
    category_id: Optional[str] = None

class HealthScore(BaseModel):
    total_score: int  # 0-100
    reserve_score: int  # 0-30
    expense_ratio_score: int  # 0-30
    consistency_score: int  # 0-20
    goals_score: int  # 0-20
    level: str  # "Crítico", "Atenção", "Bom", "Excelente"
    tips: List[str]

# ==================== END GAMIFICATION MODELS ====================

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    profile_photo: Optional[str] = None
    preferences: Optional[dict] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

@api_router.get("/profile")
async def get_profile(user_id: str = Depends(verify_token)):
    user_doc = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    return user_doc

@api_router.put("/profile")
async def update_profile(profile: ProfileUpdate, user_id: str = Depends(verify_token)):
    update_data = {}
    if profile.name is not None:
        update_data['name'] = profile.name
    if profile.profile_photo is not None:
        update_data['profile_photo'] = profile.profile_photo
    if profile.preferences is not None:
        update_data['preferences'] = profile.preferences
    
    if update_data:
        result = await db.users.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
    
    updated_user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    return updated_user

@api_router.post("/profile/change-password")
async def change_password(data: PasswordChange, user_id: str = Depends(verify_token)):
    user_doc = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify current password
    if not bcrypt.checkpw(data.current_password.encode('utf-8'), user_doc['password'].encode('utf-8')):
        raise HTTPException(status_code=400, detail="Senha atual incorreta")
    
    # Hash new password
    hashed_password = bcrypt.hashpw(data.new_password.encode('utf-8'), bcrypt.gensalt())
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"password": hashed_password.decode('utf-8')}}
    )
    
    return {"message": "Senha alterada com sucesso"}

@api_router.delete("/transactions/delete-all")
async def delete_all_transactions(user_id: str = Depends(verify_token)):
    result = await db.transactions.delete_many({"user_id": user_id})
    return {"message": f"Todas as {result.deleted_count} transações foram excluídas com sucesso", "count": result.deleted_count}

# ==================== GAMIFICATION ENDPOINTS ====================

# Badge definitions - these are the available badges
BADGE_DEFINITIONS = [
    {"name": "Mês sem Juros", "description": "Completou um mês sem pagar juros", "icon": "🎉", "criteria": "no_interest_month"},
    {"name": "Poupador Iniciante", "description": "Fez o primeiro depósito na reserva de emergência", "icon": "🌱", "criteria": "first_reserve_deposit"},
    {"name": "Meta de Reserva Batida", "description": "Atingiu 100% de uma meta financeira", "icon": "🏆", "criteria": "goal_completed"},
    {"name": "Constância é Tudo", "description": "3 meses consecutivos com aportes na poupança", "icon": "📈", "criteria": "consecutive_savings"},
    {"name": "Família Unida", "description": "Todos os membros contribuíram no mês", "icon": "👨‍👩‍👧‍👦", "criteria": "all_members_contributed"},
    {"name": "Economizador Master", "description": "Taxa de poupança acima de 30%", "icon": "💎", "criteria": "high_savings_rate"},
    {"name": "Organizador Financeiro", "description": "Categorizou todas as transações do mês", "icon": "📊", "criteria": "all_categorized"},
    {"name": "Reserva Sólida", "description": "Reserva de emergência >= 6 meses de despesas", "icon": "🛡️", "criteria": "solid_reserve"},
]

@api_router.get("/gamification/badges")
async def get_user_badges(user_id: str = Depends(verify_token)):
    """Get all badges and their unlock status for the user"""
    user_badges = await db.badges.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    unlocked_badges = {b['criteria']: b for b in user_badges}
    
    result = []
    for badge_def in BADGE_DEFINITIONS:
        unlocked = unlocked_badges.get(badge_def['criteria'])
        result.append({
            **badge_def,
            "unlocked": unlocked is not None,
            "unlocked_at": unlocked.get('unlocked_at') if unlocked else None
        })
    
    return result

@api_router.post("/gamification/check-badges")
async def check_and_unlock_badges(user_id: str = Depends(verify_token)):
    """Check and automatically unlock badges based on user activity"""
    unlocked = []
    
    # Get user data
    transactions = await db.transactions.find({"user_id": user_id}, {"_id": 0}).to_list(10000)
    goals = await db.goals.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    members = await db.family_members.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    categories = await db.categories.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    
    reserve_category = next((c for c in categories if c['name'] == 'Reserva de Emergência'), None)
    reserve_category_id = reserve_category['id'] if reserve_category else None
    
    for trans in transactions:
        if isinstance(trans.get('date'), str):
            trans['date'] = datetime.fromisoformat(trans['date'])
    
    current_month = datetime.now(timezone.utc).month
    current_year = datetime.now(timezone.utc).year
    
    # Check: First reserve deposit
    if reserve_category_id:
        reserve_transactions = [t for t in transactions if t.get('category_id') == reserve_category_id or t.get('is_reserve_deposit')]
        if reserve_transactions:
            existing = await db.badges.find_one({"user_id": user_id, "criteria": "first_reserve_deposit"})
            if not existing:
                badge = {"id": str(uuid.uuid4()), "user_id": user_id, "criteria": "first_reserve_deposit", "unlocked_at": datetime.now(timezone.utc).isoformat()}
                await db.badges.insert_one(badge)
                unlocked.append({"name": "Poupador Iniciante", "icon": "🌱"})
    
    # Check: Goal completed
    completed_goals = [g for g in goals if g.get('current_amount', 0) >= g.get('target_amount', float('inf'))]
    if completed_goals:
        existing = await db.badges.find_one({"user_id": user_id, "criteria": "goal_completed"})
        if not existing:
            badge = {"id": str(uuid.uuid4()), "user_id": user_id, "criteria": "goal_completed", "unlocked_at": datetime.now(timezone.utc).isoformat()}
            await db.badges.insert_one(badge)
            unlocked.append({"name": "Meta de Reserva Batida", "icon": "🏆"})
    
    # Check: High savings rate (>30%)
    current_month_trans = [t for t in transactions if t['date'].month == current_month and t['date'].year == current_year]
    income = sum(t['amount'] for t in current_month_trans if t['type'] == 'receita')
    expenses = sum(t['amount'] for t in current_month_trans if t['type'] == 'despesa')
    if income > 0:
        savings_rate = ((income - expenses) / income) * 100
        if savings_rate >= 30:
            existing = await db.badges.find_one({"user_id": user_id, "criteria": "high_savings_rate"})
            if not existing:
                badge = {"id": str(uuid.uuid4()), "user_id": user_id, "criteria": "high_savings_rate", "unlocked_at": datetime.now(timezone.utc).isoformat()}
                await db.badges.insert_one(badge)
                unlocked.append({"name": "Economizador Master", "icon": "💎"})
    
    # Check: All transactions categorized
    uncategorized = [t for t in current_month_trans if not t.get('category_id')]
    if current_month_trans and not uncategorized:
        existing = await db.badges.find_one({"user_id": user_id, "criteria": "all_categorized"})
        if not existing:
            badge = {"id": str(uuid.uuid4()), "user_id": user_id, "criteria": "all_categorized", "unlocked_at": datetime.now(timezone.utc).isoformat()}
            await db.badges.insert_one(badge)
            unlocked.append({"name": "Organizador Financeiro", "icon": "📊"})
    
    # Check: Solid reserve (6+ months expenses)
    avg_monthly_expenses = expenses if expenses > 0 else 1
    reserve_total = sum(t['amount'] for t in transactions if t.get('is_reserve_deposit') or (reserve_category_id and t.get('category_id') == reserve_category_id and t['type'] == 'receita'))
    if reserve_total >= avg_monthly_expenses * 6:
        existing = await db.badges.find_one({"user_id": user_id, "criteria": "solid_reserve"})
        if not existing:
            badge = {"id": str(uuid.uuid4()), "user_id": user_id, "criteria": "solid_reserve", "unlocked_at": datetime.now(timezone.utc).isoformat()}
            await db.badges.insert_one(badge)
            unlocked.append({"name": "Reserva Sólida", "icon": "🛡️"})
    
    # Check: All members contributed
    if members:
        member_ids = {m['id'] for m in members}
        contributing_members = {t['member_id'] for t in current_month_trans if t.get('member_id')}
        if member_ids and member_ids == contributing_members:
            existing = await db.badges.find_one({"user_id": user_id, "criteria": "all_members_contributed"})
            if not existing:
                badge = {"id": str(uuid.uuid4()), "user_id": user_id, "criteria": "all_members_contributed", "unlocked_at": datetime.now(timezone.utc).isoformat()}
                await db.badges.insert_one(badge)
                unlocked.append({"name": "Família Unida", "icon": "👨‍👩‍👧‍👦"})
    
    return {"unlocked": unlocked, "count": len(unlocked)}

# Family Challenges
@api_router.post("/gamification/challenges")
async def create_challenge(challenge: FamilyChallengeCreate, user_id: str = Depends(verify_token)):
    challenge_obj = FamilyChallenge(**challenge.model_dump())
    doc = challenge_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    if doc.get('deadline'):
        doc['deadline'] = doc['deadline'].isoformat()
    doc['user_id'] = user_id
    await db.challenges.insert_one(doc)
    return challenge_obj

@api_router.get("/gamification/challenges")
async def get_challenges(user_id: str = Depends(verify_token)):
    challenges = await db.challenges.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    for challenge in challenges:
        if isinstance(challenge.get('created_at'), str):
            challenge['created_at'] = datetime.fromisoformat(challenge['created_at'])
        if challenge.get('deadline') and isinstance(challenge['deadline'], str):
            challenge['deadline'] = datetime.fromisoformat(challenge['deadline'])
    return challenges

@api_router.put("/gamification/challenges/{challenge_id}")
async def update_challenge(challenge_id: str, challenge: FamilyChallengeCreate, user_id: str = Depends(verify_token)):
    update_data = challenge.model_dump()
    if update_data.get('deadline'):
        update_data['deadline'] = update_data['deadline'].isoformat()
    result = await db.challenges.update_one({"id": challenge_id, "user_id": user_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Challenge not found")
    updated = await db.challenges.find_one({"id": challenge_id}, {"_id": 0})
    return updated

@api_router.post("/gamification/challenges/{challenge_id}/progress")
async def update_challenge_progress(challenge_id: str, amount: float, user_id: str = Depends(verify_token)):
    """Update the current_amount of a challenge"""
    challenge = await db.challenges.find_one({"id": challenge_id, "user_id": user_id}, {"_id": 0})
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    new_amount = challenge.get('current_amount', 0) + amount
    is_completed = new_amount >= challenge.get('target_amount', float('inf'))
    
    update_data = {"current_amount": new_amount}
    if is_completed and not challenge.get('is_completed'):
        update_data['is_completed'] = True
        update_data['completed_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.challenges.update_one({"id": challenge_id, "user_id": user_id}, {"$set": update_data})
    
    updated = await db.challenges.find_one({"id": challenge_id}, {"_id": 0})
    return updated

@api_router.delete("/gamification/challenges/{challenge_id}")
async def delete_challenge(challenge_id: str, user_id: str = Depends(verify_token)):
    result = await db.challenges.delete_one({"id": challenge_id, "user_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return {"message": "Challenge deleted successfully"}

# Health Score
@api_router.get("/gamification/health-score", response_model=HealthScore)
async def get_health_score(user_id: str = Depends(verify_token)):
    """Calculate the financial health score (0-100) based on multiple criteria"""
    
    transactions = await db.transactions.find({"user_id": user_id}, {"_id": 0}).to_list(10000)
    goals = await db.goals.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    categories = await db.categories.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    
    for trans in transactions:
        if isinstance(trans.get('date'), str):
            trans['date'] = datetime.fromisoformat(trans['date'])
    
    current_month = datetime.now(timezone.utc).month
    current_year = datetime.now(timezone.utc).year
    
    # Calculate current month's income and expenses
    current_month_trans = [t for t in transactions if t['date'].month == current_month and t['date'].year == current_year]
    month_income = sum(t['amount'] for t in current_month_trans if t['type'] == 'receita')
    month_expenses = sum(t['amount'] for t in current_month_trans if t['type'] == 'despesa')
    
    # Calculate reserve
    reserve_category = next((c for c in categories if c['name'] == 'Reserva de Emergência'), None)
    reserve_category_id = reserve_category['id'] if reserve_category else None
    reserve_total = 0
    for trans in transactions:
        if trans.get('is_reserve_deposit'):
            reserve_total += trans['amount']
        elif trans.get('is_reserve_withdrawal'):
            reserve_total -= trans['amount']
        elif reserve_category_id and trans.get('category_id') == reserve_category_id:
            if trans.get('type') == 'receita':
                reserve_total += trans['amount']
            else:
                reserve_total -= trans['amount']
    
    tips = []
    
    # 1. Reserve Score (0-30) - based on months of expenses covered
    months_covered = reserve_total / month_expenses if month_expenses > 0 else 0
    if months_covered >= 6:
        reserve_score = 30
    elif months_covered >= 3:
        reserve_score = 20
    elif months_covered >= 1:
        reserve_score = 10
    else:
        reserve_score = 0
        tips.append("💡 Construa uma reserva de emergência de pelo menos 3-6 meses de despesas")
    
    # 2. Expense Ratio Score (0-30) - expenses should be < 70% of income
    if month_income > 0:
        expense_ratio = month_expenses / month_income
        if expense_ratio <= 0.5:
            expense_ratio_score = 30
        elif expense_ratio <= 0.7:
            expense_ratio_score = 20
        elif expense_ratio <= 0.9:
            expense_ratio_score = 10
        else:
            expense_ratio_score = 0
            tips.append("💡 Suas despesas estão muito altas. Tente reduzir para menos de 70% da renda")
    else:
        expense_ratio_score = 0
        tips.append("💡 Registre suas receitas para uma análise mais precisa")
    
    # 3. Consistency Score (0-20) - based on savings pattern in last 3 months
    consistency_score = 0
    months_with_savings = 0
    for i in range(3):
        check_month = current_month - i if current_month - i > 0 else 12 + (current_month - i)
        check_year = current_year if current_month - i > 0 else current_year - 1
        month_trans = [t for t in transactions if t['date'].month == check_month and t['date'].year == check_year]
        m_income = sum(t['amount'] for t in month_trans if t['type'] == 'receita')
        m_expenses = sum(t['amount'] for t in month_trans if t['type'] == 'despesa')
        if m_income > m_expenses:
            months_with_savings += 1
    
    if months_with_savings == 3:
        consistency_score = 20
    elif months_with_savings == 2:
        consistency_score = 13
    elif months_with_savings == 1:
        consistency_score = 7
    else:
        tips.append("💡 Tente economizar algo todo mês, mesmo que seja pouco")
    
    # 4. Goals Score (0-20) - based on progress towards goals
    if goals:
        total_progress = 0
        for goal in goals:
            progress = min(goal.get('current_amount', 0) / goal.get('target_amount', 1), 1.0)
            total_progress += progress
        avg_progress = total_progress / len(goals)
        goals_score = int(avg_progress * 20)
        if avg_progress < 0.5:
            tips.append("💡 Continue investindo nas suas metas. Pequenos aportes fazem diferença!")
    else:
        goals_score = 0
        tips.append("💡 Defina metas financeiras para acompanhar seu progresso")
    
    # Calculate total score
    total_score = reserve_score + expense_ratio_score + consistency_score + goals_score
    
    # Determine level
    if total_score >= 80:
        level = "Excelente"
    elif total_score >= 60:
        level = "Bom"
    elif total_score >= 40:
        level = "Atenção"
    else:
        level = "Crítico"
    
    return HealthScore(
        total_score=total_score,
        reserve_score=reserve_score,
        expense_ratio_score=expense_ratio_score,
        consistency_score=consistency_score,
        goals_score=goals_score,
        level=level,
        tips=tips[:3]  # Return top 3 tips
    )

# ==================== END GAMIFICATION ENDPOINTS ====================

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
