import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY         = os.getenv('SECRET_KEY', 'change-me-in-production')
    JWT_SECRET         = os.getenv('JWT_SECRET', 'jwt-secret-change-me')
    JWT_EXPIRY_HOURS   = int(os.getenv('JWT_EXPIRY_HOURS', 2)) # 2 hours access
    REFRESH_SECRET     = os.getenv('REFRESH_SECRET', 'refresh-token-secret-change-me')

    # Database: fallback to local SQLite for frictionless evaluation
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        # Resolve to instance/smartmeet.db
        base_dir = os.path.abspath(os.path.dirname(__file__))
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(base_dir, 'instance', 'smartmeet.db')}"
    else:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ChromaDB persistent storage location
    CHROMA_PATH = os.getenv('CHROMA_PATH', os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'chroma_db'))

    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')   # NEVER expose to frontend

    # AWS S3
    AWS_ACCESS_KEY     = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_KEY     = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_S3_BUCKET      = os.getenv('AWS_S3_BUCKET', 'smartmeet-reports')
    AWS_REGION         = os.getenv('AWS_REGION', 'us-east-1')

    # SendGrid & SMTP
    SENDGRID_API_KEY   = os.getenv('SENDGRID_API_KEY')
    FROM_EMAIL         = os.getenv('FROM_EMAIL', 'reports@smartmeet.ai')
    
    # Optional Local SMTP Server Configuration (Local Fallback)
    SMTP_SERVER        = os.getenv('SMTP_SERVER', 'localhost')
    SMTP_PORT          = int(os.getenv('SMTP_PORT', 1025))  # e.g., local mailpit or python SMTP debugging server
    SMTP_USERNAME      = os.getenv('SMTP_USERNAME', '')
    SMTP_PASSWORD      = os.getenv('SMTP_PASSWORD', '')

    # Encryption
    ENCRYPTION_KEY     = os.getenv('ENCRYPTION_KEY', '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef')  # hex 32-byte default key

    # CORS
    ALLOWED_ORIGINS    = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173,https://your-dashboard.vercel.app').split(',')

