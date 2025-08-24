import os
from dotenv import load_dotenv

load_dotenv()

# JWT Configuration
JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Debug: Print JWT configuration
print(f"🔧 JWT Configuration loaded:")
print(f"   Secret Key: {JWT_SECRET_KEY[:10]}...")
print(f"   Algorithm: {JWT_ALGORITHM}")
print(f"   Expire Minutes: {JWT_ACCESS_TOKEN_EXPIRE_MINUTES}")

# Database Configuration
DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/dbname")

# Security
SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")

# Stripe Configuration
STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PUBLISHABLE_KEY: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")