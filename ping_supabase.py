import os
from supabase import create_client

# Načtení URL a klíče (GitHub je získá z tvého nastavení, viz Krok 3)
SUPABASE_URL = "https://ycwkedvzyhsofbuhludk.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_KEY:
    print("Chyba: Supabase klíč nebyl nalezen v nastavení GitHubu.")
    exit(1)

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    # Provede se bleskový dotaz do tabulky users
    supabase.table("users").select("count", count="exact").limit(1).execute()
    print("Supabase úspěšně probuzena!")
except Exception as e:
    print(f"Ping selhal: {e}")
