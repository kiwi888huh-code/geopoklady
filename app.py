from supabase import create_client
import streamlit as st
from streamlit_local_storage import LocalStorage  # <--- NOVÉ

# --- INICIALIZACE PERZISTENTNÍHO ÚLOŽIŠTĚ ---
localS = LocalStorage()  # <--- NOVÉ

# Inicializace session_state pro jméno
if "username" not in st.session_state:
    st.session_state["username"] = None

# 1. LOGIKA PŘIHLÁŠENÍ (Paměť prohlížeče -> URL -> Manuální)
# Nejdřív zkusíme, jestli si ho prohlížeč pamatuje (pro refresh na mobilu)
if st.session_state["username"] is None:
    stored_user = localS.getItem("gc_user")
    if stored_user:
        st.session_state["username"] = stored_user

# Pak zkusíme URL parametry (pro první vstup přes odkaz)
url_params = st.query_params
if "user" in url_params and st.session_state["username"] is None:
    user_val = url_params["user"].lower().strip()
    st.session_state["username"] = user_val
    localS.setItem("gc_user", user_val) # Uložíme do paměti mobilu

# Pokud pořád nikoho nemáme, ukážeme formulář
if st.session_state["username"] is None:
    st.title("Geocaching filtr – Přihlášení")
    user_input = st.text_input("Zadej svou přezdívku:").lower().strip()
    if st.button("Vstoupit"):
        if user_input:
            st.session_state["username"] = user_input
            localS.setItem("gc_user", user_input) # "Vypálíme" do mobilu
            st.rerun()
        else:
            st.error("Jméno nesmí být prázdné!")
    st.stop()

# --- ZBYTEK TVOJEHO KÓDU (Supabase, Data, UI) ---

SUPABASE_URL = "https://ycwkedvzyhsofbuhludk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inljd2tlZHZ6eWhzb2ZidWhsdWRrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3NzUxNTMsImV4cCI6MjA5MDM1MTE1M30.ai6oiGESIWk4dxIG_tFb8FOuTMEhNeaymE7eWLpTsnk"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Konstanty
CACHE_TYPES = ["💚Traditional💚","🧡Multi🧡","💙Mystery💙","🩵Virtual🩵","🌍Earthcache🌍","📬Letterbox📬","🧭Wherigo🧭","❤️Event❤️","🪾CITO🪾"]
SIZES = ["micro","small","regular","large","other"]
ATTRIBUTES = ["👶děti👶","🐶psi🐶","🛠️speciální nástroj🛠️","🚗drive-in🚗","🔭vyhlídka🔭","🌞24/7🌞"]

# ===== LOAD DATA =====
def load_data():
    try:
        res = supabase.table("treasures").select("*").eq("user_id", st.session_state["username"]).execute()
        data = res.data or []

        if not data:
            res_templates = supabase.table("treasures").select("*").is_("user_id", "null").execute()
            templates = res_templates.data or []
            
            if templates:
                for t in templates:
                    new_treasure = t.copy()
                    if "id" in new_treasure: del new_treasure["id"]
                    new_treasure["user_id"] = st.session_state["username"]
                    supabase.table("treasures").insert(new_treasure).execute()
                
                res = supabase.table("treasures").select("*").eq("user_id", st.session_state["username"]).execute()
                data = res.data or []

        clean_data = []
        for t in data:
            try:
                clean_data.append({
                    "name": str(t.get("name", "")),
                    "types": t.get("types") or [],
                    "sizes": t.get("sizes") or [],
                    "attrs": t.get("attrs") or [],
                    "terrain_min": float(t.get("terrain_min") or 0.5),
                    "terrain_max": float(t.get("terrain_max") or 5.0),
                    "difficulty_min": float(t.get("difficulty_min") or 0.5),
                    "difficulty_max": float(t.get("difficulty_max") or 5.0),
                    "fav_min": int(t.get("fav_min") or 0),
                    "remaining": max(0, int(t.get("remaining") or 0))
                })
            except: continue
        return clean_data
    except Exception as e:
        st.error(f"Chyba při načítání: {e}")
        return []

# Inicializace pokladů
if "treasures" not in st.session_state:
    st.session_state.treasures = load_data()

# Stavy UI
for key, default in {
    "show_list": False,
    "open_detail": None,
    "open_detail_result": None,
    "edit_index": None,
    "results": [],
    "confirm_use": None,
    "confirm_delete": None
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ===== SAVE =====
def save():
    try:
        supabase.table("treasures").delete().eq("user_id", st.session_state["username"]).execute()
        for t in st.session_state.treasures:
            t["user_id"] = st.session_state["username"]
            supabase.table("treasures").insert(t).execute()
        st.toast("Uloženo do databáze!", icon="💾")
    except Exception as e:
        st.error(f"Chyba při ukládání: {e}")

# --- SIDEBAR S ODHLÁŠENÍM ---
with st.sidebar:
    st.write(f"Přihlášen: **{st.session_state['username']}**")
    if st.button("Odhlásit se"):
        localS.removeItem("gc_user") # <--- Vymaže paměť v prohlížeči
        st.session_state["username"] = None
        st.rerun()

# --- HLAVNÍ OBSAH (Zadej keš) ---
st.title("Geocaching – výběr pokladů")
st.header("Zadej keš")

# Formulář keše (zůstává stejný)
cache_type = st.selectbox("Typ keše", CACHE_TYPES)
cache_size = st.selectbox("Velikost", SIZES)
cache_difficulty = st.slider("Obtížnost", 0.5, 5.0, 0.5, 0.5)
cache_terrain = st.slider("Terén", 0.5, 5.0, 0.5, 0.5)
cache_fav = st.number_input("Srdíčka", 0, 10000, 0)
cache_attrs = st.multiselect("Atributy keše", ATTRIBUTES)

def match(t, c):
    if t["types"] and c["type"] not in t["types"]: return False
    if not (t["terrain_min"] <= c["terrain"] <= t["terrain_max"]): return False
    if not (t["difficulty_min"] <= c["difficulty"] <= t["difficulty_max"]): return False
    if t["sizes"] and c["size"] not in t["sizes"]: return False
    if c["fav"] < t["fav_min"]: return False
    if not set(t["attrs"]).issubset(set(c["attrs"])): return False
    return True

if st.button("Vyhodnotit"):
    cache = {"type": cache_type, "terrain": cache_terrain, "difficulty": cache_difficulty, "size": cache_size, "fav": cache_fav, "attrs": cache_attrs}
    results = [(i, t) for i, t in enumerate(st.session_state.treasures) if match(t, cache)]
    st.session_state.results = sorted(results, key=lambda x: (x[1]["remaining"], x[1]["name"]))

# Zobrazení výsledků
st.subheader("Vhodné poklady:")
if st.session_state.results:
    for i, t in st.session_state.results:
        col1, col2, col3, col4 = st.columns([4,2,1,1])
        col1.write(t["name"])
        col2.write(t["remaining"])
        if col3.button("ℹ️", key=f"res_info_{i}"):
            st.session_state.open_detail_result = i if st.session_state.open_detail_result != i else None
        if col4.button("✅", key=f"use_{i}"):
            st.session_state.confirm_use = i

        if st.session_state.open_detail_result == i:
            st.markdown(f"**Typy:** {', '.join(t['types'])} | **T/D:** {t['terrain_min']}-{t['terrain_max']}/{t['difficulty_min']}-{t['difficulty_max']}")

        if st.session_state.confirm_use == i:
            if st.button(f"Potvrdit použití {t['name']}", key=f"conf_y_{i}"):
                if st.session_state.treasures[i]["remaining"] > 0:
                    st.session_state.treasures[i]["remaining"] -= 1
                    save()
                st.session_state.confirm_use = None
                st.rerun()
else:
    st.write("Žádný poklad nesplňuje podmínky")

# --- SEZNAM A EDITACE (Zbytek tvého kódu) ---
st.divider()
if st.button("Zobrazit / skrýt seznam pokladů"):
    st.session_state.show_list = not st.session_state.show_list

if st.session_state.show_list:
    st.header("Seznam pokladů")
    # ... (tvoje logika pro grouped_all a výpis seznamu zůstává beze změny)
    for i, t in enumerate(st.session_state.treasures):
        st.write(f"{t['name']} ({t['remaining']}x)")

# --- FORM DOLE (Přidat / Upravit) ---
st.header("Přidat / upravit poklad")
# ... (tvoje formulářové prvky name, types, sizes, atd. zůstávají stejné)
# Jen na konci při ukládání:
if st.button("Uložit poklad", key="final_save_btn"):
    new_data = {
        "name": name, "types": types, "terrain_min": terrain_min, "terrain_max": terrain_max,
        "difficulty_min": difficulty_min, "difficulty_max": difficulty_max, "sizes": sizes,
        "fav_min": fav_min, "attrs": attrs, "remaining": remaining
    }
    if st.session_state.edit_index is None:
        st.session_state.treasures.append(new_data)
    else:
        st.session_state.treasures[st.session_state.edit_index] = new_data
        st.session_state.edit_index = None
    save()
    st.rerun()
