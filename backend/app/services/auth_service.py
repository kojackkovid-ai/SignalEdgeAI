import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from app.config import settings
from fastapi import HTTPException, status, Depends, Header

class AuthService:
    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.expire_minutes = settings.access_token_expire_minutes

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt directly"""
        # bcrypt automatically handles passwords up to 72 bytes
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash using bcrypt directly"""
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def _decode_token(self, token: str) -> str:
        """Decode and validate JWT token, return user_id with expiration check"""
        try:
            # JWT decode automatically validates expiration via 'exp' claim
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing user information"
                )
            
            # Verify token has expiration claim
            exp: int = payload.get("exp")
            if exp is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing expiration"
                )
            
            return user_id
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired. Please login again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def get_current_user(self, authorization: Optional[str] = Header(None)) -> str:
        """Extract user ID from Bearer token in Authorization header"""
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authorization header"
            )
        
        # Extract token from "Bearer <token>"
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme"
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format"
            )
        
        return self._decode_token(token)

    async def register_user(self, db, email: str, password: str, username: str):
        """Register new user"""
        from sqlalchemy import select
        from app.models.db_models import User
        
        # Check if user already exists
        result = await db.execute(select(User).where((User.email == email) | (User.username == username)))
        existing_user = result.scalars().first()
        if existing_user:
            raise ValueError("User already exists")
        
        # Create new user
        user = User(
            email=email,
            username=username,
            password_hash=self.hash_password(password),
            subscription_tier="free"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def authenticate_user(self, db, email: str, password: str):
        """Authenticate user"""
        from sqlalchemy import select
        from app.models.db_models import User
        
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        if not user or not self.verify_password(password, user.password_hash):
            return None
        return user

    async def get_user_by_id(self, db, user_id: str):
        """Get user by ID"""
        from sqlalchemy import select
        from app.models.db_models import User
        
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()


# Module-level function for FastAPI Depends() compatibility
def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    """Extract user ID from Bearer token in Authorization header"""
    auth_service = AuthService()
    return auth_service.get_current_user(authorization)
