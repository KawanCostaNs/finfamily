"""
FinFamily API - Self-hosted Financial Management
Refactored to use SQLite and serve frontend statically
"""
from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from contextlib import asynccontextmanager
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
import hashlib
import json

# Database
from database import init_db, get_db_context

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Paths
STATIC_DIR = ROOT_DIR / 'static'
DATA_DIR = ROOT_DIR / 'data'

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Configuration
SECRET_KEY = os.environ.get('JWT_SECRET', os.environ.get('SECRET_KEY', 'change-this-secret-key-in-production'))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# ==================== LIFESPAN ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    logging.info("🚀 FinFamily API started")
    yield
    # Shutdown
    logging.info("👋 FinFamily API shutting down")

# ==================== APP SETUP ====================

app = FastAPI(
    title="FinFamily API", 
    version="2.0.0",
    description="Self-hosted Family Financial Management",
    lifespan=lifespan
)

api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== PYDANTIC MODELS ====================

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    is_admin: bool = False
    is_approved: bool = False
    profile_photo: Optional[str] = None
    preferences: Optional[dict] = None
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
    is_fixed: bool = False
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
    member_id: Optional[str] = None
    bank_id: Optional[str] = None
    is_reserve_deposit: bool = False
    is_reserve_withdrawal: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TransactionCreate(BaseModel):
    date: datetime
    description: str
    amount: float
    type: str
    category_id: Optional[str] = None
    member_id: Optional[str] = None
    bank_id: Optional[str] = None
    is_reserve_deposit: bool = False
    is_reserve_withdrawal: bool = False

class TransactionUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = None
    type: Optional[str] = None
    category_id: Optional[str] = None
    member_id: Optional[str] = None
    bank_id: Optional[str] = None

class BulkCategorize(BaseModel):
    transaction_ids: List[str]
    category_id: str

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

class CategorizationRuleCreate(BaseModel):
    keyword: str
    category_id: str
    match_type: str = "contains"
    is_active: bool = True
    priority: int = 0

class FamilyChallengeCreate(BaseModel):
    name: str
    description: str
    target_amount: float
    reward: str
    deadline: Optional[datetime] = None
    category_id: Optional[str] = None

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    profile_photo: Optional[str] = None
    preferences: Optional[dict] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

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

class HealthScore(BaseModel):
    total_score: int
    reserve_score: int
    expense_ratio_score: int
    consistency_score: int
    goals_score: int
    level: str
    tips: List[str]

# ==================== AUTH HELPERS ====================

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

def create_token(user_id: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    return jwt.encode({"sub": user_id, "exp": expires}, SECRET_KEY, algorithm=ALGORITHM)

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def row_to_dict(row) -> dict:
    """Convert sqlite3 Row to dict"""
    return dict(row) if row else None

# ==================== HEALTH CHECK ====================

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "finamily-api", "version": "2.0.0", "database": "sqlite"}

# ==================== AUTH ENDPOINTS ====================

@api_router.post("/auth/register")
async def register(user_data: UserCreate):
    async with get_db_context() as db:
        # Check if email exists
        cursor = await db.execute("SELECT id FROM users WHERE email = ?", (user_data.email,))
        if await cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Check if first user
        cursor = await db.execute("SELECT COUNT(*) as count FROM users")
        row = await cursor.fetchone()
        is_first_user = row['count'] == 0
        
        # Create user
        user = User(
            email=user_data.email,
            name=user_data.name,
            is_admin=is_first_user,
            is_approved=is_first_user
        )
        
        await db.execute('''
            INSERT INTO users (id, email, name, password, is_admin, is_approved, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user.id, user.email, user.name, hash_password(user_data.password), 
              int(user.is_admin), int(user.is_approved), user.created_at.isoformat()))
        
        # Create default categories for first user
        if is_first_user:
            default_categories = [
                ("Reserva de Emergência", "especial", True),
                ("Alimentação", "despesa", True),
                ("Transporte", "despesa", True),
                ("Saúde", "despesa", True),
                ("Lazer", "despesa", True),
                ("Educação", "despesa", True),
                ("Moradia", "despesa", True),
                ("Salário", "receita", True),
                ("Freelance", "receita", True),
            ]
            for name, cat_type, is_fixed in default_categories:
                cat_id = str(uuid.uuid4())
                await db.execute('''
                    INSERT INTO categories (id, user_id, name, type, is_fixed, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (cat_id, user.id, name, cat_type, int(is_fixed), datetime.now(timezone.utc).isoformat()))
        
        await db.commit()
        
        if not is_first_user:
            raise HTTPException(status_code=202, detail="Conta criada! Aguarde aprovação do administrador.")
        
        return Token(access_token=create_token(user.id), token_type="bearer", user=user)

@api_router.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    async with get_db_context() as db:
        cursor = await db.execute("SELECT * FROM users WHERE email = ?", (user_data.email,))
        row = await cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        user_dict = row_to_dict(row)
        
        if not verify_password(user_data.password, user_dict['password']):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        if not user_dict['is_approved']:
            raise HTTPException(status_code=403, detail="Conta aguardando aprovação do administrador")
        
        user = User(
            id=user_dict['id'],
            email=user_dict['email'],
            name=user_dict['name'],
            is_admin=bool(user_dict['is_admin']),
            is_approved=bool(user_dict['is_approved']),
            profile_photo=user_dict.get('profile_photo'),
            preferences=json.loads(user_dict['preferences']) if user_dict.get('preferences') else None
        )
        
        return Token(access_token=create_token(user.id), token_type="bearer", user=user)

# ==================== ADMIN ENDPOINTS ====================

@api_router.get("/admin/users")
async def get_all_users(user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        # Check if admin
        cursor = await db.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()
        if not row or not row['is_admin']:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        cursor = await db.execute("SELECT id, email, name, is_admin, is_approved, created_at FROM users")
        rows = await cursor.fetchall()
        return [row_to_dict(r) for r in rows]

@api_router.post("/admin/approve/{target_user_id}")
async def approve_user(target_user_id: str, user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        cursor = await db.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()
        if not row or not row['is_admin']:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        await db.execute("UPDATE users SET is_approved = 1 WHERE id = ?", (target_user_id,))
        
        # Create default categories for approved user
        cursor = await db.execute("SELECT id FROM categories WHERE user_id = ?", (target_user_id,))
        if not await cursor.fetchone():
            default_categories = [
                ("Reserva de Emergência", "especial", True),
                ("Alimentação", "despesa", True),
                ("Transporte", "despesa", True),
                ("Saúde", "despesa", True),
                ("Lazer", "despesa", True),
                ("Educação", "despesa", True),
                ("Moradia", "despesa", True),
                ("Salário", "receita", True),
                ("Freelance", "receita", True),
            ]
            for name, cat_type, is_fixed in default_categories:
                cat_id = str(uuid.uuid4())
                await db.execute('''
                    INSERT INTO categories (id, user_id, name, type, is_fixed, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (cat_id, target_user_id, name, cat_type, int(is_fixed), datetime.now(timezone.utc).isoformat()))
        
        await db.commit()
        return {"message": "User approved successfully"}

@api_router.post("/admin/reject/{target_user_id}")
async def reject_user(target_user_id: str, user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        cursor = await db.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()
        if not row or not row['is_admin']:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        await db.execute("DELETE FROM users WHERE id = ? AND is_approved = 0", (target_user_id,))
        await db.commit()
        return {"message": "User rejected"}

@api_router.post("/admin/reset-password/{target_user_id}")
async def admin_reset_password(target_user_id: str, user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        cursor = await db.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()
        if not row or not row['is_admin']:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        new_password = "Reset@2025"
        await db.execute("UPDATE users SET password = ? WHERE id = ?", 
                        (hash_password(new_password), target_user_id))
        await db.commit()
        return {"message": f"Password reset to: {new_password}"}

# ==================== FAMILY MEMBERS ====================

@api_router.get("/family")
async def get_family_members(user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        cursor = await db.execute(
            "SELECT id, name, profile, created_at FROM family_members WHERE user_id = ?", 
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [row_to_dict(r) for r in rows]

@api_router.post("/family")
async def create_family_member(member: FamilyMemberCreate, user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        member_obj = FamilyMember(**member.model_dump())
        await db.execute('''
            INSERT INTO family_members (id, user_id, name, profile, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (member_obj.id, user_id, member_obj.name, member_obj.profile, 
              member_obj.created_at.isoformat()))
        await db.commit()
        return member_obj

@api_router.put("/family/{member_id}")
async def update_family_member(member_id: str, member: FamilyMemberCreate, user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        await db.execute(
            "UPDATE family_members SET name = ?, profile = ? WHERE id = ? AND user_id = ?",
            (member.name, member.profile, member_id, user_id)
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT id, name, profile, created_at FROM family_members WHERE id = ?", 
            (member_id,)
        )
        row = await cursor.fetchone()
        return row_to_dict(row)

@api_router.delete("/family/{member_id}")
async def delete_family_member(member_id: str, user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        await db.execute("DELETE FROM family_members WHERE id = ? AND user_id = ?", (member_id, user_id))
        await db.commit()
        return {"message": "Member deleted"}

# ==================== BANKS ====================

@api_router.get("/banks")
async def get_banks(user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        cursor = await db.execute(
            "SELECT id, name, active, created_at FROM banks WHERE user_id = ?", 
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [row_to_dict(r) for r in rows]

@api_router.post("/banks")
async def create_bank(bank: BankCreate, user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        bank_obj = Bank(**bank.model_dump())
        await db.execute('''
            INSERT INTO banks (id, user_id, name, active, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (bank_obj.id, user_id, bank_obj.name, int(bank_obj.active), 
              bank_obj.created_at.isoformat()))
        await db.commit()
        return bank_obj

@api_router.put("/banks/{bank_id}")
async def update_bank(bank_id: str, bank: BankCreate, user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        await db.execute(
            "UPDATE banks SET name = ?, active = ? WHERE id = ? AND user_id = ?",
            (bank.name, int(bank.active), bank_id, user_id)
        )
        await db.commit()
        cursor = await db.execute("SELECT id, name, active, created_at FROM banks WHERE id = ?", (bank_id,))
        row = await cursor.fetchone()
        return row_to_dict(row)

@api_router.delete("/banks/{bank_id}")
async def delete_bank(bank_id: str, user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        await db.execute("DELETE FROM banks WHERE id = ? AND user_id = ?", (bank_id, user_id))
        await db.commit()
        return {"message": "Bank deleted"}

# ==================== CATEGORIES ====================

@api_router.get("/categories")
async def get_categories(user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        cursor = await db.execute(
            "SELECT id, name, type, is_fixed, created_at FROM categories WHERE user_id = ?", 
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [row_to_dict(r) for r in rows]

@api_router.post("/categories")
async def create_category(category: CategoryCreate, user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        cat_obj = Category(**category.model_dump())
        await db.execute('''
            INSERT INTO categories (id, user_id, name, type, is_fixed, created_at)
            VALUES (?, ?, ?, ?, 0, ?)
        ''', (cat_obj.id, user_id, cat_obj.name, cat_obj.type, cat_obj.created_at.isoformat()))
        await db.commit()
        return cat_obj

@api_router.put("/categories/{category_id}")
async def update_category(category_id: str, category: CategoryCreate, user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        await db.execute(
            "UPDATE categories SET name = ?, type = ? WHERE id = ? AND user_id = ? AND is_fixed = 0",
            (category.name, category.type, category_id, user_id)
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT id, name, type, is_fixed, created_at FROM categories WHERE id = ?", 
            (category_id,)
        )
        row = await cursor.fetchone()
        return row_to_dict(row)

@api_router.delete("/categories/{category_id}")
async def delete_category(category_id: str, user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        await db.execute(
            "DELETE FROM categories WHERE id = ? AND user_id = ? AND is_fixed = 0", 
            (category_id, user_id)
        )
        await db.commit()
        return {"message": "Category deleted"}

# ==================== TRANSACTIONS ====================

@api_router.get("/transactions")
async def get_transactions(
    month: Optional[int] = None, 
    year: Optional[int] = None,
    category_id: Optional[str] = None,
    user_id: str = Depends(verify_token)
):
    async with get_db_context() as db:
        query = "SELECT * FROM transactions WHERE user_id = ?"
        params = [user_id]
        
        if category_id:
            query += " AND category_id = ?"
            params.append(category_id)
        
        query += " ORDER BY date DESC"
        
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        transactions = [row_to_dict(r) for r in rows]
        
        # Filter by month/year in Python (SQLite date handling)
        if month and year:
            transactions = [
                t for t in transactions 
                if datetime.fromisoformat(t['date']).month == month 
                and datetime.fromisoformat(t['date']).year == year
            ]
        
        return transactions

@api_router.post("/transactions")
async def create_transaction(transaction: TransactionCreate, user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        trans_obj = Transaction(**transaction.model_dump())
        await db.execute('''
            INSERT INTO transactions (id, user_id, date, description, amount, type, 
                category_id, member_id, bank_id, is_reserve_deposit, is_reserve_withdrawal, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (trans_obj.id, user_id, trans_obj.date.isoformat(), trans_obj.description,
              trans_obj.amount, trans_obj.type, trans_obj.category_id, trans_obj.member_id,
              trans_obj.bank_id, int(trans_obj.is_reserve_deposit), 
              int(trans_obj.is_reserve_withdrawal), trans_obj.created_at.isoformat()))
        await db.commit()
        return trans_obj

@api_router.put("/transactions/{transaction_id}")
async def update_transaction(transaction_id: str, transaction: TransactionUpdate, user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        updates = []
        params = []
        
        update_dict = transaction.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if value is not None:
                updates.append(f"{key} = ?")
                params.append(value)
        
        if updates:
            params.extend([transaction_id, user_id])
            await db.execute(
                f"UPDATE transactions SET {', '.join(updates)} WHERE id = ? AND user_id = ?",
                params
            )
            await db.commit()
        
        cursor = await db.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
        row = await cursor.fetchone()
        return row_to_dict(row)

@api_router.delete("/transactions/{transaction_id}")
async def delete_transaction(transaction_id: str, user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        await db.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (transaction_id, user_id))
        await db.commit()
        return {"message": "Transaction deleted"}

@api_router.post("/transactions/bulk-categorize")
async def bulk_categorize(data: BulkCategorize, user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        for trans_id in data.transaction_ids:
            await db.execute(
                "UPDATE transactions SET category_id = ? WHERE id = ? AND user_id = ?",
                (data.category_id, trans_id, user_id)
            )
        await db.commit()
        return {"message": f"Updated {len(data.transaction_ids)} transactions"}

@api_router.delete("/transactions/delete-all")
async def delete_all_transactions(user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        cursor = await db.execute("SELECT COUNT(*) as count FROM transactions WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        count = row['count']
        
        await db.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
        await db.commit()
        return {"message": f"Todas as {count} transações foram excluídas", "count": count}

# ==================== IMPORT ====================

async def apply_categorization_rules(description: str, user_id: str, db) -> Optional[str]:
    """Apply categorization rules to find matching category"""
    cursor = await db.execute(
        "SELECT keyword, category_id, match_type FROM categorization_rules WHERE user_id = ? AND is_active = 1 ORDER BY priority DESC",
        (user_id,)
    )
    rules = await cursor.fetchall()
    
    description_lower = description.lower()
    
    for rule in rules:
        keyword_lower = rule['keyword'].lower()
        match_type = rule['match_type']
        
        if match_type == 'contains' and keyword_lower in description_lower:
            return rule['category_id']
        elif match_type == 'starts_with' and description_lower.startswith(keyword_lower):
            return rule['category_id']
        elif match_type == 'exact' and description_lower == keyword_lower:
            return rule['category_id']
    
    return None

@api_router.post("/transactions/import")
async def import_transactions(
    file: UploadFile = File(...),
    member_id: str = Form(...),
    bank_id: str = Form(...),
    user_id: str = Depends(verify_token)
):
    async with get_db_context() as db:
        content = await file.read()
        filename = file.filename.lower()
        
        transactions = []
        duplicates_count = 0
        auto_categorized = 0
        
        # Get existing hashes for duplicate detection
        cursor = await db.execute(
            "SELECT unique_hash FROM transactions WHERE user_id = ?", (user_id,)
        )
        existing_hashes = {row['unique_hash'] for row in await cursor.fetchall() if row['unique_hash']}
        
        if filename.endswith('.csv'):
            try:
                text_content = content.decode('utf-8')
            except UnicodeDecodeError:
                text_content = content.decode('latin-1')
            
            reader = csv.DictReader(io.StringIO(text_content), delimiter=';')
            
            for row in reader:
                date_str = row.get('Data Lançamento') or row.get('Data') or row.get('date', '')
                description = row.get('Descrição') or row.get('description', '')
                amount_str = row.get('Valor') or row.get('amount', '0')
                
                if not description:
                    continue
                
                # Parse amount
                amount_str = str(amount_str).replace('R$', '').replace('.', '').replace(',', '.').strip()
                try:
                    amount = float(amount_str)
                except ValueError:
                    continue
                
                # Parse date
                trans_date = datetime.now(timezone.utc)
                if date_str:
                    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
                        try:
                            trans_date = datetime.strptime(date_str.strip(), fmt).replace(tzinfo=timezone.utc)
                            break
                        except ValueError:
                            continue
                
                # Determine type
                trans_type = 'despesa' if amount < 0 else 'receita'
                
                # Create unique hash
                unique_hash = hashlib.md5(
                    f"{trans_date.date()}{description}{abs(amount)}".encode()
                ).hexdigest()
                
                if unique_hash in existing_hashes:
                    duplicates_count += 1
                    continue
                
                existing_hashes.add(unique_hash)
                
                # Apply categorization rules
                category_id = await apply_categorization_rules(description, user_id, db)
                if category_id:
                    auto_categorized += 1
                
                trans_id = str(uuid.uuid4())
                transactions.append({
                    'id': trans_id,
                    'user_id': user_id,
                    'date': trans_date.isoformat(),
                    'description': description,
                    'amount': abs(amount),
                    'type': trans_type,
                    'category_id': category_id,
                    'member_id': member_id,
                    'bank_id': bank_id,
                    'unique_hash': unique_hash,
                    'created_at': datetime.now(timezone.utc).isoformat()
                })
        
        # Insert transactions
        for trans in transactions:
            await db.execute('''
                INSERT INTO transactions (id, user_id, date, description, amount, type, 
                    category_id, member_id, bank_id, unique_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (trans['id'], trans['user_id'], trans['date'], trans['description'],
                  trans['amount'], trans['type'], trans['category_id'], trans['member_id'],
                  trans['bank_id'], trans['unique_hash'], trans['created_at']))
        
        await db.commit()
        
        message = f"Importadas {len(transactions)} transações"
        if duplicates_count > 0:
            message += f" ({duplicates_count} duplicatas ignoradas)"
        if auto_categorized > 0:
            message += f" ({auto_categorized} auto-categorizadas)"
        
        return {
            "message": message,
            "count": len(transactions),
            "duplicates": duplicates_count,
            "auto_categorized": auto_categorized
        }

# ==================== DASHBOARD ====================

@api_router.get("/dashboard/summary")
async def get_dashboard_summary(month: int, year: int, user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        cursor = await db.execute("SELECT * FROM transactions WHERE user_id = ?", (user_id,))
        all_transactions = [row_to_dict(r) for r in await cursor.fetchall()]
        
        # Parse dates and filter
        for t in all_transactions:
            t['date_obj'] = datetime.fromisoformat(t['date'])
        
        # Previous balance (all transactions before this month)
        previous_trans = [t for t in all_transactions 
                        if (t['date_obj'].year < year) or 
                           (t['date_obj'].year == year and t['date_obj'].month < month)]
        previous_income = sum(t['amount'] for t in previous_trans if t['type'] == 'receita')
        previous_expenses = sum(t['amount'] for t in previous_trans if t['type'] == 'despesa')
        previous_balance = previous_income - previous_expenses
        
        # Current month
        current_trans = [t for t in all_transactions 
                        if t['date_obj'].year == year and t['date_obj'].month == month]
        month_income = sum(t['amount'] for t in current_trans if t['type'] == 'receita')
        month_expenses = sum(t['amount'] for t in current_trans if t['type'] == 'despesa')
        
        final_balance = previous_balance + month_income - month_expenses
        
        return DashboardSummary(
            previous_balance=previous_balance,
            month_income=month_income,
            month_expenses=month_expenses,
            final_balance=final_balance
        )

@api_router.get("/dashboard/emergency-reserve")
async def get_emergency_reserve(user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        # Get emergency reserve category
        cursor = await db.execute(
            "SELECT id FROM categories WHERE user_id = ? AND name = 'Reserva de Emergência'",
            (user_id,)
        )
        cat_row = await cursor.fetchone()
        
        if not cat_row:
            return {"total": 0, "message": "Configure a categoria Reserva de Emergência"}
        
        category_id = cat_row['id']
        
        # Get transactions for this category
        cursor = await db.execute(
            "SELECT amount, type, category_id, is_reserve_deposit, is_reserve_withdrawal FROM transactions WHERE user_id = ? AND (category_id = ? OR is_reserve_deposit = 1 OR is_reserve_withdrawal = 1)",
            (user_id, category_id)
        )
        transactions = await cursor.fetchall()
        
        total = 0
        for t in transactions:
            if t['is_reserve_deposit'] or (t['category_id'] == category_id and t['type'] == 'receita'):
                total += t['amount']
            elif t['is_reserve_withdrawal']:
                total -= t['amount']
        
        # Get average monthly expenses
        cursor = await db.execute(
            "SELECT AVG(amount) as avg FROM transactions WHERE user_id = ? AND type = 'despesa'",
            (user_id,)
        )
        avg_row = await cursor.fetchone()
        avg_expenses = avg_row['avg'] or 0
        
        months_covered = total / avg_expenses if avg_expenses > 0 else 0
        
        if months_covered >= 6:
            message = "Excelente! Mais de 6 meses de despesas guardadas"
        elif months_covered >= 3:
            message = f"Bom progresso! {months_covered:.1f} meses de despesas guardadas"
        else:
            message = f"Continue construindo sua reserva ({months_covered:.1f} meses)"
        
        return {"total": total, "months_covered": months_covered, "message": message}

@api_router.get("/dashboard/category-chart")
async def get_category_chart(month: int, year: int, user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        cursor = await db.execute("SELECT * FROM transactions WHERE user_id = ? AND type = 'despesa'", (user_id,))
        transactions = [row_to_dict(r) for r in await cursor.fetchall()]
        
        # Filter by month/year
        transactions = [
            t for t in transactions 
            if datetime.fromisoformat(t['date']).month == month 
            and datetime.fromisoformat(t['date']).year == year
        ]
        
        # Get categories
        cursor = await db.execute("SELECT id, name FROM categories WHERE user_id = ?", (user_id,))
        categories = {r['id']: r['name'] for r in await cursor.fetchall()}
        
        # Aggregate by category
        category_totals = {}
        for t in transactions:
            cat_name = categories.get(t['category_id'], 'Sem categoria')
            category_totals[cat_name] = category_totals.get(cat_name, 0) + t['amount']
        
        total = sum(category_totals.values())
        
        result = [
            CategoryChart(
                category=cat, 
                amount=amount, 
                percentage=round((amount/total*100) if total > 0 else 0, 2)
            )
            for cat, amount in category_totals.items()
        ]
        
        return sorted(result, key=lambda x: x.amount, reverse=True)

@api_router.get("/dashboard/monthly-comparison")
async def get_monthly_comparison(year: int, user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        cursor = await db.execute("SELECT * FROM transactions WHERE user_id = ?", (user_id,))
        transactions = [row_to_dict(r) for r in await cursor.fetchall()]
        
        # Parse dates
        for t in transactions:
            t['date_obj'] = datetime.fromisoformat(t['date'])
        
        # Filter by year
        year_trans = [t for t in transactions if t['date_obj'].year == year]
        
        month_names = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        result = []
        
        for month_num in range(1, 13):
            month_trans = [t for t in year_trans if t['date_obj'].month == month_num]
            income = sum(t['amount'] for t in month_trans if t['type'] == 'receita')
            expenses = sum(t['amount'] for t in month_trans if t['type'] == 'despesa')
            result.append(MonthlyComparison(month=month_names[month_num-1], income=income, expenses=expenses))
        
        return result

# ==================== GOALS ====================

@api_router.get("/goals")
async def get_goals(user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        cursor = await db.execute("SELECT * FROM goals WHERE user_id = ?", (user_id,))
        rows = await cursor.fetchall()
        return [row_to_dict(r) for r in rows]

@api_router.post("/goals")
async def create_goal(goal: GoalCreate, user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        goal_obj = Goal(**goal.model_dump())
        await db.execute('''
            INSERT INTO goals (id, user_id, name, description, target_amount, current_amount, 
                deadline, image_url, monthly_contribution, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (goal_obj.id, user_id, goal_obj.name, goal_obj.description, goal_obj.target_amount,
              goal_obj.current_amount, goal_obj.deadline.isoformat() if goal_obj.deadline else None,
              goal_obj.image_url, goal_obj.monthly_contribution, goal_obj.created_at.isoformat()))
        await db.commit()
        return goal_obj

@api_router.put("/goals/{goal_id}")
async def update_goal(goal_id: str, goal: GoalCreate, user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        await db.execute('''
            UPDATE goals SET name = ?, description = ?, target_amount = ?, 
                deadline = ?, image_url = ?, monthly_contribution = ?
            WHERE id = ? AND user_id = ?
        ''', (goal.name, goal.description, goal.target_amount,
              goal.deadline.isoformat() if goal.deadline else None,
              goal.image_url, goal.monthly_contribution, goal_id, user_id))
        await db.commit()
        cursor = await db.execute("SELECT * FROM goals WHERE id = ?", (goal_id,))
        row = await cursor.fetchone()
        return row_to_dict(row)

@api_router.delete("/goals/{goal_id}")
async def delete_goal(goal_id: str, user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        await db.execute("DELETE FROM goals WHERE id = ? AND user_id = ?", (goal_id, user_id))
        await db.commit()
        return {"message": "Goal deleted"}

@api_router.post("/goals/{goal_id}/contribute")
async def contribute_to_goal(goal_id: str, contribution: GoalContribution, user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        await db.execute(
            "UPDATE goals SET current_amount = current_amount + ? WHERE id = ? AND user_id = ?",
            (contribution.amount, goal_id, user_id)
        )
        await db.commit()
        cursor = await db.execute("SELECT * FROM goals WHERE id = ?", (goal_id,))
        row = await cursor.fetchone()
        return row_to_dict(row)

# ==================== CATEGORIZATION RULES ====================

@api_router.get("/categorization-rules")
async def get_categorization_rules(user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        cursor = await db.execute(
            "SELECT * FROM categorization_rules WHERE user_id = ? ORDER BY priority DESC",
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [row_to_dict(r) for r in rows]

@api_router.post("/categorization-rules")
async def create_categorization_rule(rule: CategorizationRuleCreate, user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        rule_id = str(uuid.uuid4())
        await db.execute('''
            INSERT INTO categorization_rules (id, user_id, keyword, category_id, match_type, is_active, priority, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (rule_id, user_id, rule.keyword, rule.category_id, rule.match_type,
              int(rule.is_active), rule.priority, datetime.now(timezone.utc).isoformat()))
        await db.commit()
        return {"id": rule_id, **rule.model_dump()}

@api_router.put("/categorization-rules/{rule_id}")
async def update_categorization_rule(rule_id: str, rule: CategorizationRuleCreate, user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        await db.execute('''
            UPDATE categorization_rules SET keyword = ?, category_id = ?, match_type = ?, 
                is_active = ?, priority = ?
            WHERE id = ? AND user_id = ?
        ''', (rule.keyword, rule.category_id, rule.match_type, int(rule.is_active),
              rule.priority, rule_id, user_id))
        await db.commit()
        cursor = await db.execute("SELECT * FROM categorization_rules WHERE id = ?", (rule_id,))
        row = await cursor.fetchone()
        return row_to_dict(row)

@api_router.delete("/categorization-rules/{rule_id}")
async def delete_categorization_rule(rule_id: str, user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        await db.execute("DELETE FROM categorization_rules WHERE id = ? AND user_id = ?", (rule_id, user_id))
        await db.commit()
        return {"message": "Rule deleted"}

# ==================== PROFILE ====================

@api_router.get("/profile")
async def get_profile(user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        cursor = await db.execute(
            "SELECT id, email, name, is_admin, is_approved, profile_photo, preferences, created_at FROM users WHERE id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_dict = row_to_dict(row)
        if user_dict.get('preferences'):
            user_dict['preferences'] = json.loads(user_dict['preferences'])
        return user_dict

@api_router.put("/profile")
async def update_profile(profile: ProfileUpdate, user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        updates = []
        params = []
        
        if profile.name:
            updates.append("name = ?")
            params.append(profile.name)
        if profile.profile_photo:
            updates.append("profile_photo = ?")
            params.append(profile.profile_photo)
        if profile.preferences:
            updates.append("preferences = ?")
            params.append(json.dumps(profile.preferences))
        
        if updates:
            params.append(user_id)
            await db.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", params)
            await db.commit()
        
        return {"message": "Profile updated"}

@api_router.post("/profile/change-password")
async def change_password(data: PasswordChange, user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        cursor = await db.execute("SELECT password FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()
        
        if not verify_password(data.current_password, row['password']):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        
        await db.execute("UPDATE users SET password = ? WHERE id = ?",
                        (hash_password(data.new_password), user_id))
        await db.commit()
        return {"message": "Password changed successfully"}

# ==================== GAMIFICATION ====================

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
    async with get_db_context() as db:
        cursor = await db.execute("SELECT criteria, unlocked_at FROM badges WHERE user_id = ?", (user_id,))
        unlocked = {r['criteria']: r['unlocked_at'] for r in await cursor.fetchall()}
        
        return [
            {
                **badge,
                "unlocked": badge['criteria'] in unlocked,
                "unlocked_at": unlocked.get(badge['criteria'])
            }
            for badge in BADGE_DEFINITIONS
        ]

@api_router.post("/gamification/check-badges")
async def check_and_unlock_badges(user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        unlocked = []
        
        # Get user data
        cursor = await db.execute("SELECT * FROM transactions WHERE user_id = ?", (user_id,))
        transactions = [row_to_dict(r) for r in await cursor.fetchall()]
        
        cursor = await db.execute("SELECT * FROM goals WHERE user_id = ?", (user_id,))
        goals = [row_to_dict(r) for r in await cursor.fetchall()]
        
        cursor = await db.execute("SELECT id FROM categories WHERE user_id = ? AND name = 'Reserva de Emergência'", (user_id,))
        reserve_cat = await cursor.fetchone()
        reserve_category_id = reserve_cat['id'] if reserve_cat else None
        
        # Parse dates
        for t in transactions:
            t['date_obj'] = datetime.fromisoformat(t['date'])
        
        current_month = datetime.now(timezone.utc).month
        current_year = datetime.now(timezone.utc).year
        
        # Check: First reserve deposit
        if reserve_category_id:
            reserve_trans = [t for t in transactions if t.get('category_id') == reserve_category_id or t.get('is_reserve_deposit')]
            if reserve_trans:
                cursor = await db.execute("SELECT id FROM badges WHERE user_id = ? AND criteria = 'first_reserve_deposit'", (user_id,))
                if not await cursor.fetchone():
                    badge_id = str(uuid.uuid4())
                    await db.execute("INSERT INTO badges (id, user_id, criteria, unlocked_at) VALUES (?, ?, ?, ?)",
                                    (badge_id, user_id, 'first_reserve_deposit', datetime.now(timezone.utc).isoformat()))
                    unlocked.append({"name": "Poupador Iniciante", "icon": "🌱"})
        
        # Check: Goal completed
        completed_goals = [g for g in goals if g.get('current_amount', 0) >= g.get('target_amount', float('inf'))]
        if completed_goals:
            cursor = await db.execute("SELECT id FROM badges WHERE user_id = ? AND criteria = 'goal_completed'", (user_id,))
            if not await cursor.fetchone():
                badge_id = str(uuid.uuid4())
                await db.execute("INSERT INTO badges (id, user_id, criteria, unlocked_at) VALUES (?, ?, ?, ?)",
                                (badge_id, user_id, 'goal_completed', datetime.now(timezone.utc).isoformat()))
                unlocked.append({"name": "Meta de Reserva Batida", "icon": "🏆"})
        
        # Check: High savings rate (>30%)
        current_trans = [t for t in transactions if t['date_obj'].month == current_month and t['date_obj'].year == current_year]
        income = sum(t['amount'] for t in current_trans if t['type'] == 'receita')
        expenses = sum(t['amount'] for t in current_trans if t['type'] == 'despesa')
        
        if income > 0 and ((income - expenses) / income) >= 0.3:
            cursor = await db.execute("SELECT id FROM badges WHERE user_id = ? AND criteria = 'high_savings_rate'", (user_id,))
            if not await cursor.fetchone():
                badge_id = str(uuid.uuid4())
                await db.execute("INSERT INTO badges (id, user_id, criteria, unlocked_at) VALUES (?, ?, ?, ?)",
                                (badge_id, user_id, 'high_savings_rate', datetime.now(timezone.utc).isoformat()))
                unlocked.append({"name": "Economizador Master", "icon": "💎"})
        
        await db.commit()
        return {"unlocked": unlocked, "count": len(unlocked)}

@api_router.get("/gamification/health-score", response_model=HealthScore)
async def get_health_score(user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        cursor = await db.execute("SELECT * FROM transactions WHERE user_id = ?", (user_id,))
        transactions = [row_to_dict(r) for r in await cursor.fetchall()]
        
        cursor = await db.execute("SELECT * FROM goals WHERE user_id = ?", (user_id,))
        goals = [row_to_dict(r) for r in await cursor.fetchall()]
        
        cursor = await db.execute("SELECT id FROM categories WHERE user_id = ? AND name = 'Reserva de Emergência'", (user_id,))
        reserve_cat = await cursor.fetchone()
        reserve_category_id = reserve_cat['id'] if reserve_cat else None
        
        for t in transactions:
            t['date_obj'] = datetime.fromisoformat(t['date'])
        
        current_month = datetime.now(timezone.utc).month
        current_year = datetime.now(timezone.utc).year
        
        # Current month data
        current_trans = [t for t in transactions if t['date_obj'].month == current_month and t['date_obj'].year == current_year]
        month_income = sum(t['amount'] for t in current_trans if t['type'] == 'receita')
        month_expenses = sum(t['amount'] for t in current_trans if t['type'] == 'despesa')
        
        # Reserve calculation
        reserve_total = 0
        if reserve_category_id:
            for t in transactions:
                if t.get('is_reserve_deposit') or (t.get('category_id') == reserve_category_id and t['type'] == 'receita'):
                    reserve_total += t['amount']
                elif t.get('is_reserve_withdrawal'):
                    reserve_total -= t['amount']
        
        tips = []
        
        # 1. Reserve Score (0-30)
        months_covered = reserve_total / month_expenses if month_expenses > 0 else 0
        if months_covered >= 6:
            reserve_score = 30
        elif months_covered >= 3:
            reserve_score = 20
        elif months_covered >= 1:
            reserve_score = 10
        else:
            reserve_score = 0
            tips.append("💡 Construa uma reserva de emergência de 3-6 meses de despesas")
        
        # 2. Expense Ratio Score (0-30)
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
                tips.append("💡 Reduza despesas para menos de 70% da renda")
        else:
            expense_ratio_score = 0
            tips.append("💡 Registre suas receitas para análise completa")
        
        # 3. Consistency Score (0-20)
        months_with_savings = 0
        for i in range(3):
            check_month = current_month - i if current_month - i > 0 else 12 + (current_month - i)
            check_year = current_year if current_month - i > 0 else current_year - 1
            month_trans = [t for t in transactions if t['date_obj'].month == check_month and t['date_obj'].year == check_year]
            m_income = sum(t['amount'] for t in month_trans if t['type'] == 'receita')
            m_expenses = sum(t['amount'] for t in month_trans if t['type'] == 'despesa')
            if m_income > m_expenses:
                months_with_savings += 1
        
        consistency_score = {3: 20, 2: 13, 1: 7}.get(months_with_savings, 0)
        if months_with_savings == 0:
            tips.append("💡 Tente economizar algo todo mês")
        
        # 4. Goals Score (0-20)
        if goals:
            total_progress = sum(min(g.get('current_amount', 0) / g.get('target_amount', 1), 1.0) for g in goals)
            goals_score = int((total_progress / len(goals)) * 20)
        else:
            goals_score = 0
            tips.append("💡 Defina metas financeiras para acompanhar progresso")
        
        total_score = reserve_score + expense_ratio_score + consistency_score + goals_score
        
        level = "Crítico" if total_score < 40 else "Atenção" if total_score < 60 else "Bom" if total_score < 80 else "Excelente"
        
        return HealthScore(
            total_score=total_score,
            reserve_score=reserve_score,
            expense_ratio_score=expense_ratio_score,
            consistency_score=consistency_score,
            goals_score=goals_score,
            level=level,
            tips=tips[:3]
        )

# ==================== CHALLENGES ====================

@api_router.get("/gamification/challenges")
async def get_challenges(user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        cursor = await db.execute("SELECT * FROM challenges WHERE user_id = ?", (user_id,))
        rows = await cursor.fetchall()
        return [row_to_dict(r) for r in rows]

@api_router.post("/gamification/challenges")
async def create_challenge(challenge: FamilyChallengeCreate, user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        challenge_id = str(uuid.uuid4())
        await db.execute('''
            INSERT INTO challenges (id, user_id, name, description, target_amount, current_amount, 
                reward, deadline, category_id, is_active, is_completed, created_at)
            VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, 1, 0, ?)
        ''', (challenge_id, user_id, challenge.name, challenge.description, challenge.target_amount,
              challenge.reward, challenge.deadline.isoformat() if challenge.deadline else None,
              challenge.category_id, datetime.now(timezone.utc).isoformat()))
        await db.commit()
        return {"id": challenge_id, **challenge.model_dump()}

@api_router.post("/gamification/challenges/{challenge_id}/progress")
async def update_challenge_progress(challenge_id: str, amount: float, user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        cursor = await db.execute("SELECT * FROM challenges WHERE id = ? AND user_id = ?", (challenge_id, user_id))
        challenge = await cursor.fetchone()
        
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        
        new_amount = challenge['current_amount'] + amount
        is_completed = new_amount >= challenge['target_amount']
        
        if is_completed and not challenge['is_completed']:
            await db.execute(
                "UPDATE challenges SET current_amount = ?, is_completed = 1, completed_at = ? WHERE id = ?",
                (new_amount, datetime.now(timezone.utc).isoformat(), challenge_id)
            )
        else:
            await db.execute("UPDATE challenges SET current_amount = ? WHERE id = ?", (new_amount, challenge_id))
        
        await db.commit()
        
        cursor = await db.execute("SELECT * FROM challenges WHERE id = ?", (challenge_id,))
        return row_to_dict(await cursor.fetchone())

@api_router.delete("/gamification/challenges/{challenge_id}")
async def delete_challenge(challenge_id: str, user_id: str = Depends(verify_token)):
    async with get_db_context() as db:
        await db.execute("DELETE FROM challenges WHERE id = ? AND user_id = ?", (challenge_id, user_id))
        await db.commit()
        return {"message": "Challenge deleted"}

# ==================== INCLUDE ROUTER ====================

app.include_router(api_router)

# ==================== STATIC FILES (Frontend) ====================

# Mount static files if directory exists (for production with built frontend)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR / "static")), name="static")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve React frontend - catch-all route for SPA"""
        # Skip API routes
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404)
        
        # Try to serve the requested file
        file_path = STATIC_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        
        # Fall back to index.html for SPA routing
        index_path = STATIC_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        
        raise HTTPException(status_code=404, detail="Frontend not found")
