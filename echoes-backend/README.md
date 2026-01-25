# Echoes Backend

A turn-based RPG backend integrated with Twitch, featuring the Spirit Blossom theme from League of Legends.

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)

### Run with Docker

```bash
# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app
```

The API will be available at `http://localhost:8000`

### Local Development

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -e .

# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Run migrations
alembic upgrade head

# Start the development server
uvicorn src.main:app --reload
```

## 📚 API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🗄️ Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## 🌱 Seed Data

```bash
python scripts/seed_data.py
```

## 📁 Project Structure

```
echoes-backend/
├── src/
│   ├── domain/          # Business entities & value objects
│   ├── application/     # Use cases & DTOs
│   ├── infrastructure/  # Database, external services
│   ├── presentation/    # API routes & schemas
│   └── core/            # Game engine (combat, effects)
├── alembic/             # Database migrations
└── scripts/             # Utility scripts
```

## 🎮 Features

- **Combat System**: Turn-based PvE with spell effects
- **Equipment**: Weapons (with spells), armor, artifacts, blessings
- **Echo Gauge**: Resource for ultimate abilities
- **Progression**: XP, levels, item upgrades
- **Twitch Integration**: OAuth authentication
