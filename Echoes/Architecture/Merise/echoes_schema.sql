-- ============================================
-- ECHOES - Script de création de base de données
-- PostgreSQL 14+
-- ============================================

-- Extension pour UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- TYPES ENUM
-- ============================================

CREATE TYPE item_type AS ENUM ('WEAPON', 'HEAD', 'ARMOR', 'ARTIFACT', 'BLESSING', 'CONSUMABLE');
CREATE TYPE rarity AS ENUM ('COMMON', 'UNCOMMON', 'RARE', 'EPIC', 'LEGENDARY');
CREATE TYPE damage_type AS ENUM ('PHYSICAL', 'MAGIC', 'TRUE', 'MIXED', 'STASIS');
CREATE TYPE spell_type AS ENUM ('BASIC', 'SKILL', 'ULTIMATE');
CREATE TYPE equipment_slot AS ENUM ('WEAPON_PRIMARY', 'WEAPON_SECONDARY', 'HEAD', 'ARMOR', 'ARTIFACT', 'BLESSING', 'CONSUMABLE');
CREATE TYPE combat_status AS ENUM ('PENDING', 'IN_PROGRESS', 'PLAYER_TURN', 'MONSTER_TURN', 'VICTORY', 'DEFEAT', 'ABANDONED');
CREATE TYPE tick_trigger AS ENUM ('ON_TURN_START', 'ON_TURN_END', 'ON_HIT', 'ON_DAMAGED', 'IMMEDIATE');
CREATE TYPE quest_type AS ENUM ('DAILY', 'WEEKLY', 'STORY', 'EVENT');
CREATE TYPE achievement_category AS ENUM ('COMBAT', 'EXPLORATION', 'COLLECTION', 'SOCIAL', 'MASTERY');
CREATE TYPE leaderboard_type AS ENUM ('GLOBAL_LEVEL', 'ACHIEVEMENTS_COUNT', 'BOSS_SPEEDRUN', 'TOTAL_MONSTERS_KILLED');

-- ============================================
-- CORE DOMAIN
-- ============================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    twitch_id VARCHAR(50) UNIQUE NOT NULL,
    username VARCHAR(100) NOT NULL,
    is_profile_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE players (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    level INTEGER NOT NULL DEFAULT 1 CHECK (level >= 1),
    current_xp BIGINT NOT NULL DEFAULT 0 CHECK (current_xp >= 0),
    xp_to_next_level BIGINT NOT NULL DEFAULT 100,
    gold INTEGER NOT NULL DEFAULT 0 CHECK (gold >= 0),
    stat_points_available INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- ITEMS - BLUEPRINTS
-- ============================================

CREATE TABLE item_blueprints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    item_type item_type NOT NULL,
    rarity rarity NOT NULL DEFAULT 'COMMON',
    level_requirement INTEGER DEFAULT 1,
    max_level INTEGER DEFAULT 100,
    is_tradeable BOOLEAN DEFAULT TRUE,
    -- Base stats
    base_max_hp INTEGER DEFAULT 0,
    base_ad INTEGER DEFAULT 0,
    base_ap INTEGER DEFAULT 0,
    base_armor INTEGER DEFAULT 0,
    base_mr INTEGER DEFAULT 0,
    base_speed INTEGER DEFAULT 0,
    base_crit_chance DECIMAL(5,2) DEFAULT 0,
    -- Scaling per level
    scaling_hp_per_level DECIMAL(5,2) DEFAULT 0,
    scaling_ad_per_level DECIMAL(5,2) DEFAULT 0,
    scaling_ap_per_level DECIMAL(5,2) DEFAULT 0,
    scaling_armor_per_level DECIMAL(5,2) DEFAULT 0,
    scaling_mr_per_level DECIMAL(5,2) DEFAULT 0
);

CREATE TABLE weapon_blueprints (
    id UUID PRIMARY KEY REFERENCES item_blueprints(id) ON DELETE CASCADE,
    damage_type damage_type NOT NULL DEFAULT 'PHYSICAL'
);

CREATE TABLE equipment_blueprints (
    id UUID PRIMARY KEY REFERENCES item_blueprints(id) ON DELETE CASCADE,
    slot equipment_slot NOT NULL,
    passive_effects JSONB DEFAULT '[]'
);

CREATE TABLE consumable_blueprints (
    id UUID PRIMARY KEY REFERENCES item_blueprints(id) ON DELETE CASCADE,
    effects JSONB NOT NULL DEFAULT '[]',
    uses_per_combat INTEGER DEFAULT 1
);

-- ============================================
-- ITEMS - INSTANCES
-- ============================================

CREATE TABLE item_instances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    blueprint_id UUID NOT NULL REFERENCES item_blueprints(id) ON DELETE CASCADE,
    owner_id UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    item_level INTEGER NOT NULL DEFAULT 1 CHECK (item_level >= 1),
    item_xp INTEGER DEFAULT 0 CHECK (item_xp >= 0),
    item_xp_to_next_level INTEGER DEFAULT 100,
    is_equipped BOOLEAN DEFAULT FALSE,
    equipped_slot equipment_slot,
    acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- PLAYER EQUIPMENT LOADOUT
-- ============================================

CREATE TABLE player_equipment_loadout (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID UNIQUE NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    weapon_primary_id UUID REFERENCES item_instances(id) ON DELETE SET NULL,
    weapon_secondary_id UUID REFERENCES item_instances(id) ON DELETE SET NULL,
    head_id UUID REFERENCES item_instances(id) ON DELETE SET NULL,
    armor_id UUID REFERENCES item_instances(id) ON DELETE SET NULL,
    artifact_id UUID REFERENCES item_instances(id) ON DELETE SET NULL,
    blessing_id UUID REFERENCES item_instances(id) ON DELETE SET NULL,
    consumable_id UUID REFERENCES item_instances(id) ON DELETE SET NULL
);

-- ============================================
-- SPELLS
-- ============================================

CREATE TABLE spells (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    weapon_blueprint_id UUID NOT NULL REFERENCES weapon_blueprints(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    spell_type spell_type NOT NULL DEFAULT 'BASIC',
    spell_order INTEGER DEFAULT 1 CHECK (spell_order BETWEEN 1 AND 3),
    cooldown_turns INTEGER DEFAULT 0,
    echo_cost INTEGER DEFAULT 0,
    effects JSONB NOT NULL DEFAULT '[]'
);

-- ============================================
-- MONSTERS
-- ============================================

CREATE TABLE loot_tables (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL
);

CREATE TABLE monster_blueprints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    base_level INTEGER NOT NULL DEFAULT 1,
    ai_behavior VARCHAR(50) DEFAULT 'basic',
    loot_table_id UUID REFERENCES loot_tables(id) ON DELETE SET NULL,
    xp_reward INTEGER NOT NULL,
    gold_reward_min INTEGER NOT NULL,
    gold_reward_max INTEGER NOT NULL,
    is_boss BOOLEAN DEFAULT FALSE,
    sprite_key VARCHAR(100),
    -- Base stats
    base_max_hp INTEGER NOT NULL,
    base_ad INTEGER DEFAULT 0,
    base_ap INTEGER DEFAULT 0,
    base_armor INTEGER DEFAULT 0,
    base_mr INTEGER DEFAULT 0,
    base_speed INTEGER DEFAULT 10,
    -- Scaling
    scaling_hp_per_level DECIMAL(5,2) DEFAULT 0,
    scaling_ad_per_level DECIMAL(5,2) DEFAULT 0,
    scaling_armor_per_level DECIMAL(5,2) DEFAULT 0
);

CREATE TABLE monster_abilities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    monster_blueprint_id UUID NOT NULL REFERENCES monster_blueprints(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    cooldown INTEGER DEFAULT 0,
    priority INTEGER DEFAULT 1,
    condition_expr VARCHAR(200),
    effects JSONB NOT NULL DEFAULT '[]'
);

CREATE TABLE loot_table_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    loot_table_id UUID NOT NULL REFERENCES loot_tables(id) ON DELETE CASCADE,
    item_blueprint_id UUID NOT NULL REFERENCES item_blueprints(id) ON DELETE CASCADE,
    weight INTEGER NOT NULL DEFAULT 100,
    min_quantity INTEGER DEFAULT 1,
    max_quantity INTEGER DEFAULT 1,
    min_player_level INTEGER DEFAULT 1
);

-- ============================================
-- COMBAT
-- ============================================

CREATE TABLE combat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    monster_blueprint_id UUID NOT NULL REFERENCES monster_blueprints(id) ON DELETE CASCADE,
    monster_level INTEGER NOT NULL,
    status combat_status DEFAULT 'PENDING',
    turn_count INTEGER DEFAULT 0 CHECK (turn_count >= 0),
    current_turn_entity VARCHAR(20),
    -- Player combat state
    player_current_hp INTEGER NOT NULL CHECK (player_current_hp >= 0),
    player_max_hp INTEGER NOT NULL,
    player_echo_current INTEGER DEFAULT 0,
    player_echo_max INTEGER DEFAULT 100,
    player_statuses JSONB DEFAULT '{}',
    player_gauges JSONB DEFAULT '{}',
    -- Monster combat state
    monster_current_hp INTEGER NOT NULL CHECK (monster_current_hp >= 0),
    monster_max_hp INTEGER NOT NULL,
    monster_statuses JSONB DEFAULT '{}',
    -- Timestamps
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP
);

CREATE TABLE combat_spell_cooldowns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    combat_session_id UUID NOT NULL REFERENCES combat_sessions(id) ON DELETE CASCADE,
    spell_id UUID NOT NULL REFERENCES spells(id) ON DELETE CASCADE,
    remaining_turns INTEGER NOT NULL,
    UNIQUE(combat_session_id, spell_id)
);

CREATE TABLE combat_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    combat_session_id UUID NOT NULL REFERENCES combat_sessions(id) ON DELETE CASCADE,
    turn INTEGER NOT NULL,
    actor VARCHAR(20) NOT NULL,
    action_type VARCHAR(50),
    spell_id UUID,
    damage_dealt INTEGER,
    damage_type damage_type,
    was_critical BOOLEAN DEFAULT FALSE,
    echo_gained INTEGER DEFAULT 0,
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- EFFECT ENGINE
-- ============================================

CREATE TABLE status_definitions (
    code VARCHAR(50) PRIMARY KEY,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    icon_key VARCHAR(100),
    is_debuff BOOLEAN DEFAULT TRUE,
    is_stackable BOOLEAN DEFAULT FALSE,
    max_stacks INTEGER DEFAULT 1,
    tick_trigger tick_trigger,
    tick_effect JSONB
);

-- ============================================
-- DUNGEONS
-- ============================================

CREATE TABLE dungeons (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    level_requirement INTEGER DEFAULT 1,
    recommended_level INTEGER,
    boss_blueprint_id UUID REFERENCES monster_blueprints(id) ON DELETE SET NULL,
    background_key VARCHAR(100)
);

CREATE TABLE dungeon_monster_sequence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dungeon_id UUID NOT NULL REFERENCES dungeons(id) ON DELETE CASCADE,
    monster_blueprint_id UUID NOT NULL REFERENCES monster_blueprints(id) ON DELETE CASCADE,
    sequence_order INTEGER NOT NULL,
    monster_level_override INTEGER
);

CREATE TABLE player_dungeon_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    dungeon_id UUID NOT NULL REFERENCES dungeons(id) ON DELETE CASCADE,
    is_unlocked BOOLEAN DEFAULT FALSE,
    best_clear_time_ms INTEGER,
    clear_count INTEGER DEFAULT 0,
    last_cleared_at TIMESTAMP,
    UNIQUE(player_id, dungeon_id)
);

-- ============================================
-- PROGRESSION
-- ============================================

CREATE TABLE achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category achievement_category,
    condition_type VARCHAR(50) NOT NULL,
    condition_value INTEGER NOT NULL,
    condition_target_id UUID,
    reward_xp INTEGER DEFAULT 0,
    reward_gold INTEGER DEFAULT 0,
    reward_item_blueprint_id UUID REFERENCES item_blueprints(id) ON DELETE SET NULL,
    icon_key VARCHAR(100),
    is_hidden BOOLEAN DEFAULT FALSE
);

CREATE TABLE player_achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    achievement_id UUID NOT NULL REFERENCES achievements(id) ON DELETE CASCADE,
    progress INTEGER DEFAULT 0,
    is_completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP,
    UNIQUE(player_id, achievement_id)
);

CREATE TABLE quests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    quest_type quest_type NOT NULL,
    objective_type VARCHAR(50) NOT NULL,
    objective_target INTEGER NOT NULL,
    objective_target_id UUID,
    reward_xp INTEGER DEFAULT 0,
    reward_gold INTEGER DEFAULT 0,
    reward_item_blueprint_id UUID REFERENCES item_blueprints(id) ON DELETE SET NULL,
    is_repeatable BOOLEAN DEFAULT FALSE,
    reset_period_hours INTEGER
);

CREATE TABLE player_quests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    quest_id UUID NOT NULL REFERENCES quests(id) ON DELETE CASCADE,
    progress INTEGER DEFAULT 0,
    is_completed BOOLEAN DEFAULT FALSE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    expires_at TIMESTAMP,
    UNIQUE(player_id, quest_id)
);

CREATE TABLE leaderboard_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    leaderboard_type leaderboard_type NOT NULL,
    score BIGINT NOT NULL,
    rank INTEGER,
    metadata JSONB,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_id, leaderboard_type)
);

-- ============================================
-- INDEXES
-- ============================================

CREATE INDEX idx_users_twitch_id ON users(twitch_id);
CREATE INDEX idx_players_user_id ON players(user_id);
CREATE INDEX idx_players_level ON players(level);
CREATE INDEX idx_item_instances_owner_id ON item_instances(owner_id);
CREATE INDEX idx_item_instances_blueprint_id ON item_instances(blueprint_id);
CREATE INDEX idx_spells_weapon_blueprint_id ON spells(weapon_blueprint_id);
CREATE INDEX idx_monster_abilities_monster_id ON monster_abilities(monster_blueprint_id);
CREATE INDEX idx_combat_sessions_player_id ON combat_sessions(player_id);
CREATE INDEX idx_combat_sessions_status ON combat_sessions(status);
CREATE INDEX idx_combat_logs_session_id ON combat_logs(combat_session_id);
CREATE INDEX idx_loot_table_entries_loot_table_id ON loot_table_entries(loot_table_id);
CREATE INDEX idx_player_achievements_player_id ON player_achievements(player_id);
CREATE INDEX idx_player_quests_player_id ON player_quests(player_id);
CREATE INDEX idx_leaderboard_entries_type_score ON leaderboard_entries(leaderboard_type, score DESC);

-- ============================================
-- TRIGGERS
-- ============================================

-- Auto-update updated_at on users
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Auto-create player_equipment_loadout when player is created
CREATE OR REPLACE FUNCTION create_player_loadout()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO player_equipment_loadout (player_id) VALUES (NEW.id);
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER create_loadout_after_player
    AFTER INSERT ON players
    FOR EACH ROW
    EXECUTE FUNCTION create_player_loadout();

-- ============================================
-- COMMENTS
-- ============================================

COMMENT ON TABLE users IS 'Comptes utilisateurs liés à Twitch (RGPD: données minimales)';
COMMENT ON TABLE players IS 'Données de jeu du joueur';
COMMENT ON TABLE item_blueprints IS 'Définitions statiques des items (partagées)';
COMMENT ON TABLE item_instances IS 'Items possédés par les joueurs (avec niveau propre)';
COMMENT ON TABLE combat_sessions IS 'Sessions de combat en cours ou terminées';
COMMENT ON TABLE status_definitions IS 'Définitions des effets de statut (BURN, FREEZE...)';
COMMENT ON COLUMN spells.effects IS 'Liste d''EffectPayload JSON: [{opcode, order, params}]';
COMMENT ON COLUMN combat_sessions.player_statuses IS 'Dict[status_code, {remaining, stacks}]';
