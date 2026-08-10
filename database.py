"""Gestion de base de datos SQLite asincrona."""
import aiosqlite
import os
from datetime import datetime, timedelta
from config import CONFIG

class Database:
    def __init__(self):
        self.db_path = CONFIG.DATABASE_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    async def init(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript("""
                CREATE TABLE IF NOT EXISTS creators (
                    discord_id INTEGER PRIMARY KEY,
                    minecraft_ign TEXT NOT NULL,
                    rank TEXT DEFAULT 'MEDIA',
                    platform TEXT,
                    followers INTEGER DEFAULT 0,
                    views INTEGER DEFAULT 0,
                    likes INTEGER DEFAULT 0,
                    points INTEGER DEFAULT 0,
                    join_date TEXT,
                    last_renewal TEXT,
                    next_renewal TEXT,
                    status TEXT DEFAULT 'ACTIVO',
                    content_count INTEGER DEFAULT 0,
                    video_count INTEGER DEFAULT 0,
                    stream_count INTEGER DEFAULT 0,
                    warnings INTEGER DEFAULT 0,
                    total_views INTEGER DEFAULT 0,
                    total_likes INTEGER DEFAULT 0,
                    youtube_link TEXT,
                    tiktok_link TEXT,
                    twitch_link TEXT,
                    instagram_link TEXT,
                    twitter_link TEXT,
                    kick_link TEXT,
                    discord_tag TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_id INTEGER,
                    minecraft_ign TEXT,
                    platform TEXT,
                    platform_link TEXT,
                    followers INTEGER,
                    avg_views INTEGER,
                    avg_likes INTEGER,
                    content_examples TEXT,
                    content_type TEXT,
                    status TEXT DEFAULT 'PENDIENTE',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    reviewed_by INTEGER,
                    review_notes TEXT
                );

                CREATE TABLE IF NOT EXISTS renewals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_id INTEGER,
                    minecraft_ign TEXT,
                    platform TEXT,
                    current_followers INTEGER,
                    content_posted TEXT,
                    video_count INTEGER,
                    stream_count INTEGER,
                    views INTEGER,
                    likes INTEGER,
                    content_links TEXT,
                    additional_stats TEXT,
                    low_activity_reason TEXT,
                    status TEXT DEFAULT 'PENDIENTE',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    reviewed_by INTEGER,
                    review_notes TEXT
                );

                CREATE TABLE IF NOT EXISTS points_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_id INTEGER,
                    points_change INTEGER,
                    reason TEXT,
                    new_total INTEGER,
                    staff_id INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS rewards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    description TEXT,
                    reward_type TEXT,
                    value TEXT,
                    available INTEGER DEFAULT 1,
                    requirements TEXT
                );

                CREATE TABLE IF NOT EXISTS rewards_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_id INTEGER,
                    reward_id INTEGER,
                    claimed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    staff_id INTEGER
                );

                CREATE TABLE IF NOT EXISTS rank_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_id INTEGER,
                    old_rank TEXT,
                    new_rank TEXT,
                    changed_by INTEGER,
                    reason TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS warnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_id INTEGER,
                    reason TEXT,
                    staff_id INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS campaigns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    objective TEXT,
                    duration_days INTEGER,
                    requirements TEXT,
                    prize TEXT,
                    points INTEGER,
                    status TEXT DEFAULT 'ACTIVO',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    end_date TEXT
                );

                CREATE TABLE IF NOT EXISTS challenges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    description TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    prize TEXT,
                    requirements TEXT,
                    points INTEGER,
                    status TEXT DEFAULT 'ACTIVO',
                    winner_id INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS creator_month (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    month TEXT,
                    year INTEGER,
                    winner_id INTEGER,
                    reward TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT,
                    target_id INTEGER,
                    staff_id INTEGER,
                    details TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS server_config (
                    guild_id INTEGER PRIMARY KEY,
                    log_channel_id INTEGER,
                    manager_role_id INTEGER,
                    staff_role_id INTEGER,
                    role_media INTEGER DEFAULT 0,
                    role_media_plus INTEGER DEFAULT 0,
                    role_famoso INTEGER DEFAULT 0,
                    role_partner INTEGER DEFAULT 0,
                    role_o_media INTEGER DEFAULT 0,
                    renewal_override TEXT,
                    setup_completed INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS points_config (
                    action_name TEXT PRIMARY KEY,
                    points INTEGER
                );
            """)
            await db.commit()

            # Agregar columnas de redes sociales si no existen (para bases antiguas)
            social_columns = [
                ("youtube_link", "TEXT"),
                ("tiktok_link", "TEXT"),
                ("twitch_link", "TEXT"),
                ("instagram_link", "TEXT"),
                ("twitter_link", "TEXT"),
                ("kick_link", "TEXT"),
                ("discord_tag", "TEXT")
            ]
            for col, ctype in social_columns:
                try:
                    await db.execute(f"ALTER TABLE creators ADD COLUMN {col} {ctype}")
                    await db.commit()
                except:
                    pass

            # Agregar columna renewal_override si no existe
            try:
                await db.execute("ALTER TABLE server_config ADD COLUMN renewal_override TEXT")
                await db.commit()
            except:
                pass

    async def execute(self, query, params=()):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(query, params)
            await db.commit()

    async def fetchone(self, query, params=()):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                return await cursor.fetchone()

    async def fetchall(self, query, params=()):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                return await cursor.fetchall()

    async def execute_and_get_id(self, query, params=()):
        """Ejecuta INSERT y devuelve el ID generado."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(query, params)
            await db.commit()
            return cursor.lastrowid

    async def get_creator(self, discord_id: int):
        return await self.fetchone(
            "SELECT * FROM creators WHERE discord_id = ?", (discord_id,)
        )

    async def add_creator(self, discord_id: int, minecraft_ign: str, rank: str,
                         platform: str, followers: int):
        join_date = datetime.now().isoformat()
        renewal_days = CONFIG.RANKS[rank]["renewal_days"] if rank != "PARTNER" else 30
        next_renewal = (datetime.now() + timedelta(days=renewal_days)).isoformat() if renewal_days else None

        await self.execute("""
            INSERT INTO creators (discord_id, minecraft_ign, rank, platform, 
                                followers, join_date, next_renewal, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVO')
        """, (discord_id, minecraft_ign, rank, platform, followers, join_date, next_renewal))

    async def log_action(self, action: str, target_id: int, staff_id: int, details: str = ""):
        await self.execute("""
            INSERT INTO activity_log (action, target_id, staff_id, details)
            VALUES (?, ?, ?, ?)
        """, (action, target_id, staff_id, details))

db = Database()
