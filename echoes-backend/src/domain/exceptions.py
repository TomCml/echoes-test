"""
Echoes Backend - Domain Exceptions
Custom exceptions for business logic errors.
"""


class DomainException(Exception):
    """Base exception for all domain errors."""
    
    def __init__(self, message: str, code: str = "DOMAIN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


# ============================================================================
# Combat Exceptions
# ============================================================================

class CombatException(DomainException):
    """Base exception for combat-related errors."""
    pass


class CombatNotFoundError(CombatException):
    """Combat session not found."""
    
    def __init__(self, combat_id: str = None):
        message = "Combat session not found"
        if combat_id:
            message = f"Combat session {combat_id} not found"
        super().__init__(message, "COMBAT_NOT_FOUND")


class CombatNotActiveError(CombatException):
    """Combat is not in an active state."""
    
    def __init__(self):
        super().__init__("Combat is not active", "COMBAT_NOT_ACTIVE")


class NotPlayerTurnError(CombatException):
    """It's not the player's turn."""
    
    def __init__(self):
        super().__init__("It's not your turn", "NOT_PLAYER_TURN")


class SpellOnCooldownError(CombatException):
    """Spell is on cooldown."""
    
    def __init__(self, spell_name: str, remaining_turns: int):
        super().__init__(
            f"{spell_name} is on cooldown ({remaining_turns} turns remaining)",
            "SPELL_ON_COOLDOWN"
        )
        self.spell_name = spell_name
        self.remaining_turns = remaining_turns


class NotEnoughEchoError(CombatException):
    """Not enough Echo to cast spell."""
    
    def __init__(self, required: int, current: int):
        super().__init__(
            f"Not enough Echo ({current}/{required})",
            "NOT_ENOUGH_ECHO"
        )
        self.required = required
        self.current = current


class NoConsumableUsesError(CombatException):
    """Consumable has no uses remaining."""
    
    def __init__(self):
        super().__init__("No consumable uses remaining", "NO_CONSUMABLE_USES")


class PlayerAlreadyInCombatError(CombatException):
    """Player already has an active combat."""
    
    def __init__(self):
        super().__init__("You already have an active combat", "ALREADY_IN_COMBAT")


# ============================================================================
# Player Exceptions
# ============================================================================

class PlayerException(DomainException):
    """Base exception for player-related errors."""
    pass


class PlayerNotFoundError(PlayerException):
    """Player not found."""
    
    def __init__(self, player_id: str = None):
        message = "Player not found"
        if player_id:
            message = f"Player {player_id} not found"
        super().__init__(message, "PLAYER_NOT_FOUND")


class NotEnoughGoldError(PlayerException):
    """Not enough gold for the operation."""
    
    def __init__(self, required: int, current: int):
        super().__init__(
            f"Not enough gold ({current}/{required})",
            "NOT_ENOUGH_GOLD"
        )
        self.required = required
        self.current = current


class LevelRequirementNotMetError(PlayerException):
    """Player doesn't meet level requirement."""
    
    def __init__(self, required: int, current: int):
        super().__init__(
            f"Level {required} required (current: {current})",
            "LEVEL_REQUIREMENT_NOT_MET"
        )


# ============================================================================
# Item Exceptions
# ============================================================================

class ItemException(DomainException):
    """Base exception for item-related errors."""
    pass


class ItemNotFoundError(ItemException):
    """Item not found."""
    
    def __init__(self, item_id: str = None):
        message = "Item not found"
        if item_id:
            message = f"Item {item_id} not found"
        super().__init__(message, "ITEM_NOT_FOUND")


class ItemNotOwnedError(ItemException):
    """Player doesn't own this item."""
    
    def __init__(self):
        super().__init__("You don't own this item", "ITEM_NOT_OWNED")


class ItemAlreadyEquippedError(ItemException):
    """Item is already equipped."""
    
    def __init__(self):
        super().__init__("Item is already equipped", "ITEM_ALREADY_EQUIPPED")


class InvalidEquipmentSlotError(ItemException):
    """Item cannot be equipped in this slot."""
    
    def __init__(self, item_type: str, slot: str):
        super().__init__(
            f"Cannot equip {item_type} in {slot} slot",
            "INVALID_EQUIPMENT_SLOT"
        )


class ItemMaxLevelError(ItemException):
    """Item is already at max level."""
    
    def __init__(self):
        super().__init__("Item is already at max level", "ITEM_MAX_LEVEL")


# ============================================================================
# Auth Exceptions
# ============================================================================

class AuthException(DomainException):
    """Base exception for authentication errors."""
    pass


class InvalidTokenError(AuthException):
    """Invalid or expired token."""
    
    def __init__(self):
        super().__init__("Invalid or expired token", "INVALID_TOKEN")


class UserNotFoundError(AuthException):
    """User not found."""
    
    def __init__(self):
        super().__init__("User not found", "USER_NOT_FOUND")


# ============================================================================
# Dungeon Exceptions
# ============================================================================

class DungeonException(DomainException):
    """Base exception for dungeon-related errors."""
    pass


class DungeonNotFoundError(DungeonException):
    """Dungeon not found."""
    
    def __init__(self, dungeon_id: str = None):
        message = "Dungeon not found"
        if dungeon_id:
            message = f"Dungeon {dungeon_id} not found"
        super().__init__(message, "DUNGEON_NOT_FOUND")


class DungeonLockedError(DungeonException):
    """Dungeon is not unlocked."""
    
    def __init__(self):
        super().__init__("Dungeon is locked", "DUNGEON_LOCKED")


# ============================================================================
# Quest Exceptions
# ============================================================================

class QuestException(DomainException):
    """Base exception for quest-related errors."""
    pass


class QuestNotFoundError(QuestException):
    """Quest not found."""
    
    def __init__(self):
        super().__init__("Quest not found", "QUEST_NOT_FOUND")


class QuestNotCompletedError(QuestException):
    """Quest is not completed yet."""
    
    def __init__(self):
        super().__init__("Quest is not completed", "QUEST_NOT_COMPLETED")


class QuestAlreadyClaimedError(QuestException):
    """Quest reward already claimed."""
    
    def __init__(self):
        super().__init__("Quest reward already claimed", "QUEST_ALREADY_CLAIMED")
