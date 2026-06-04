import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env from project root
load_dotenv()


@dataclass
class Settings:
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")


settings = Settings()
