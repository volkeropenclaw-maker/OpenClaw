"""
FridgeChef - Database Models (SQLAlchemy)
"""
import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import (
    create_engine, Column, String, Integer, Float, Boolean,
    Text, DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

load_dotenv()

DB_URL = os.getenv("DATABASE_URL", "sqlite:///fridgechef.db")
# Resolve relative SQLite paths relative to this file's directory
if DB_URL.startswith("sqlite:///") and not DB_URL.startswith("sqlite:////"):
    db_file = DB_URL[len("sqlite:///"):]
    if not os.path.isabs(db_file):
        db_file = os.path.join(os.path.dirname(__file__), db_file)
        DB_URL = f"sqlite:///{db_file}"

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    display_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    saved_recipes = relationship("SavedRecipe", back_populates="user", cascade="all, delete-orphan")
    shopping_items = relationship("ShoppingListItem", back_populates="user", cascade="all, delete-orphan")
    tracker_entries = relationship("TrackerEntry", back_populates="user", cascade="all, delete-orphan")


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    language = Column(String, default="de")
    theme = Column(String, default="light")
    units = Column(String, default="metric")
    daily_calories = Column(Integer, default=2000)
    daily_protein = Column(Integer, default=150)
    daily_carbs = Column(Integer, default=250)
    daily_fat = Column(Integer, default=65)
    staple_ingredients = Column(Text, default="")  # comma-separated

    user = relationship("User", back_populates="profile")


class SavedRecipe(Base):
    __tablename__ = "saved_recipes"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    recipe_json = Column(Text, nullable=False)
    collection_name = Column(String, default="")
    saved_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="saved_recipes")


class ShoppingListItem(Base):
    __tablename__ = "shopping_list_items"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    ingredient_name = Column(String, nullable=False)
    amount = Column(Float, default=0)
    unit = Column(String, default="")
    recipe_id = Column(String, default="")
    recipe_name = Column(String, default="")
    is_completed = Column(Boolean, default=False)

    user = relationship("User", back_populates="shopping_items")


class TrackerEntry(Base):
    __tablename__ = "tracker_entries"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    recipe_id = Column(String, default="")
    recipe_name = Column(String, nullable=False)
    servings = Column(Float, default=1)
    kcal = Column(Float, default=0)
    protein = Column(Float, default=0)
    fat = Column(Float, default=0)
    carbs = Column(Float, default=0)
    eaten_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="tracker_entries")


class AIRecipeCache(Base):
    __tablename__ = "ai_recipe_cache"

    id = Column(String, primary_key=True)
    ingredients_hash = Column(String, nullable=False, index=True)
    recipe_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get a database session."""
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


if __name__ == "__main__":
    init_db()
    print(f"✅ Database initialized at: {DB_URL}")
    db = get_db()
    from sqlalchemy import text
    tables = db.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
    print(f"Tables: {[t[0] for t in tables]}")
    db.close()
