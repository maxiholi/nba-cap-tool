import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SECRET_KEY")

if not supabase_url:
    raise RuntimeError("SUPABASE_URL is missing from backend/.env")

if not supabase_key:
    raise RuntimeError("SUPABASE_SECRET_KEY is missing from backend/.env")

supabase: Client = create_client(supabase_url, supabase_key)