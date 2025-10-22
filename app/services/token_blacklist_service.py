from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import delete
from app.models.token_blacklist import TokenBlacklist

class TokenBlacklistService:
    @staticmethod
    def blacklist_token(db: Session, jti:str, expires_at: datetime , user_id: Optional[int] = None) -> bool:
        try:
            blacklisted_token = TokenBlacklist(
                jti=jti,
                user_id = user_id if user_id is not None else 0,
                revoked=True,
                expires_at=expires_at,
            )
            db.add(blacklisted_token)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            return False
    
    @staticmethod
    def is_token_blacklisted(db: Session, jti: str) -> bool:
        """
        Return True if the token's JTI exists and is not expired.
        """
        now = datetime.now(timezone.utc)
        return (
            db.query(TokenBlacklist)
            .filter(
                TokenBlacklist.jti == jti,
                TokenBlacklist.expires_at > now,
            )
            .first()
            is not None
        )
    
    @staticmethod
    def cleanup_expired_tokens(db: Session) -> int:
        """
        Delete all blacklisted tokens whose expiration is in the past.
        Returns the number of rows deleted.
        """
        now = datetime.now(timezone.utc)
        result = db.execute(
            delete(TokenBlacklist).where(TokenBlacklist.expires_at <= now)
        )
        db.commit()
        return result.rowcount
    
    @staticmethod
    def get_blacklisted_token(db: Session, jti: str) -> Optional[TokenBlacklist]:
        """
        Retrieve a specific blacklisted token by JTI.
        Returns None if not found or expired.
        """
        now = datetime.now(timezone.utc)
        return (
            db.query(TokenBlacklist)
            .filter(
                TokenBlacklist.jti == jti,
                TokenBlacklist.expires_at > now,
            )
            .first()
        )