import os
from dotenv import load_dotenv

load_dotenv()

# JWT Configuration
JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "300"))

# Debug: Print JWT configuration
print(f"🔧 JWT Configuration loaded:")
print(f"   Secret Key: {JWT_SECRET_KEY[:10]}...")
print(f"   Algorithm: {JWT_ALGORITHM}")
print(f"   Expire Minutes: {JWT_ACCESS_TOKEN_EXPIRE_MINUTES}")

# Database Configuration
# Handle different database URL formats for Vercel
DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/dbname")

# Handle Vercel's DATABASE_URL format (they sometimes add ?sslmode=require)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Security
SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")

# Stripe Configuration
STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PUBLISHABLE_KEY: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")

# Environment
ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
DEBUG: bool = ENVIRONMENT == "development"

# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME: str = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY: str = os.getenv("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET: str = os.getenv("CLOUDINARY_API_SECRET", "")

print(f"🌍 Environment: {ENVIRONMENT}")
print(f"🐛 Debug: {DEBUG}")
print(f"🗄️ Database URL: {DATABASE_URL[:30]}..." if len(DATABASE_URL) > 30 else f"🗄️ Database URL: {DATABASE_URL}")