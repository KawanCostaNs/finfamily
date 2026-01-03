"""
SQLite Database Configuration for FinFamily
Uses aiosqlite for async operations with FastAPI
"""
import aiosqlite
import os
from pathlib import Path
from contextlib import asynccontextmanager

# Database file path - use environment variable or default to local file
DB_PATH = os.environ.get('DATABASE_PATH', str(Path(__file__).parent / 'data' / 'finamily.db'))

# Ensure data directory exists
Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

async def get_db():
    """Get database connection"""
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db

@asynccontextmanager
async def get_db_context():
    """Context manager for database connection"""
    db = await get_db()
    try:
        yield db
    finally:
        await db.close()

async def init_db():
    """Initialize database tables"""
    async with get_db_context() as db:
        # Users table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                password TEXT NOT NULL,
                is_admin INTEGER DEFAULT 0,
                is_approved INTEGER DEFAULT 0,
                profile_photo TEXT,
                preferences TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        # Family members table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS family_members (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                profile TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Banks table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS banks (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Categories table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                is_fixed INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Transactions table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                type TEXT NOT NULL,
                category_id TEXT,
                member_id TEXT,
                bank_id TEXT,
                is_reserve_deposit INTEGER DEFAULT 0,
                is_reserve_withdrawal INTEGER DEFAULT 0,
                unique_hash TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (category_id) REFERENCES categories(id),
                FOREIGN KEY (member_id) REFERENCES family_members(id),
                FOREIGN KEY (bank_id) REFERENCES banks(id)
            )
        ''')
        
        # Goals table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                target_amount REAL NOT NULL,
                current_amount REAL DEFAULT 0,
                deadline TEXT,
                image_url TEXT,
                monthly_contribution REAL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Categorization rules table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS categorization_rules (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                keyword TEXT NOT NULL,
                category_id TEXT NOT NULL,
                match_type TEXT DEFAULT 'contains',
                is_active INTEGER DEFAULT 1,
                priority INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        ''')
        
        # Badges table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS badges (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                criteria TEXT NOT NULL,
                unlocked_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, criteria)
            )
        ''')
        
        # Family challenges table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS challenges (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                target_amount REAL NOT NULL,
                current_amount REAL DEFAULT 0,
                reward TEXT,
                deadline TEXT,
                category_id TEXT,
                is_active INTEGER DEFAULT 1,
                is_completed INTEGER DEFAULT 0,
                completed_at TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Create indexes for better performance
        await db.execute('CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id)')
        await db.execute('CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date)')
        await db.execute('CREATE INDEX IF NOT EXISTS idx_categories_user ON categories(user_id)')
        await db.execute('CREATE INDEX IF NOT EXISTS idx_family_user ON family_members(user_id)')
        await db.execute('CREATE INDEX IF NOT EXISTS idx_banks_user ON banks(user_id)')
        await db.execute('CREATE INDEX IF NOT EXISTS idx_goals_user ON goals(user_id)')
        await db.execute('CREATE INDEX IF NOT EXISTS idx_rules_user ON categorization_rules(user_id)')
        
        await db.commit()
        print("✅ Database initialized successfully")
