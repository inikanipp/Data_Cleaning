import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

# Load file .env
load_dotenv()

# Ambil URL dari environment variable
# Berikan nilai default jika variabel tidak ditemukan untuk menghindari error
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL tidak ditemukan di file .env")

# Inisialisasi Engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Factory untuk Session
SessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

# Dependency untuk mendapatkan session DB di route/service
async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base

# ... (kode engine Anda)

Base = declarative_base()

# Tambahkan fungsi ini
async def init_db():
    async with engine.begin() as conn:
        # Ini akan membuat semua tabel yang terdaftar di model Anda
        await conn.run_sync(Base.metadata.create_all)