"""
Echoes Backend - Service Interfaces
Abstract interfaces for services.
"""
from abc import ABC, abstractmethod
from typing import Optional, Tuple


class IAuthService(ABC):
    """Interface for authentication service."""
    
    @abstractmethod
    async def authenticate_twitch(self, code: str) -> Tuple[str, dict]:
        """
        Authenticate via Twitch OAuth.
        Returns (jwt_token, user_data).
        """
        pass
    
    @abstractmethod
    async def validate_token(self, token: str) -> Optional[dict]:
        """
        Validate a JWT token.
        Returns user data if valid, None otherwise.
        """
        pass
    
    @abstractmethod
    def create_access_token(self, data: dict) -> str:
        """Create a new JWT access token."""
        pass


class ICombatService(ABC):
    """Interface for combat service."""
    
    @abstractmethod
    async def start_combat(self, player_id, monster_blueprint_id, monster_level: int):
        """Start a new combat session."""
        pass
    
    @abstractmethod
    async def execute_spell(self, session_id, spell_id):
        """Execute a spell in combat."""
        pass
    
    @abstractmethod
    async def execute_basic_attack(self, session_id):
        """Execute a basic attack."""
        pass
    
    @abstractmethod
    async def use_consumable(self, session_id):
        """Use the equipped consumable."""
        pass
    
    @abstractmethod
    async def flee_combat(self, session_id) -> Tuple[bool, str]:
        """Attempt to flee. Returns (success, message)."""
        pass
    
    @abstractmethod
    async def process_monster_turn(self, session_id):
        """Process the monster's turn."""
        pass
