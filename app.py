from supabase import create_client
import streamlit as st
from streamlit_local_storage import LocalStorage

# --- INICIALIZACE ---
localS = LocalStorage()

if "username" not in st.session_state:
    st.session_state["username"] = None

# --- LOGIKA PŘIHLÁŠENÍ S PAMĚTÍ ---
# 1. Zkusíme načíst z prohlížeče (pro refresh)
if st.session_state["username"] is None:
    stored_user = localS.getItem("gc_user")
    if stored_user:
        st.session_state["username"] = stored_user

# 2. Zkusíme URL parametry
url_params = st.query_params
if "user" in url_params and st.session_state["username"] is None:
    user_val = url_params["user"].lower().strip()
    st.session_state["username"] = user_val
    localS.setItem("gc_user", user_val)

# 3. Přihlašovací formulář
if st.session_state["username"] is None:
    st.title("Geocaching filtr – Přihlášení")
    user_input = st.text_input("Zadej svou přezdívku:").lower().strip()
    if st.button("Vstoupit"):
        if user_input:
            st.session_state["username"] = user_input
            localS.setItem("gc_user", user_input)
            st.rerun()
        else:
            st.error("Jméno nesmí být prázdné!")
    st.stop()

# --- KONFIGURACE DATABÁZE ---
SUPABASE_URL = "https://ycwkedvzyhsofbuhludk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inljd2tlZHZ6eWhzb2ZidWhsdWRrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3NzUxNTMsImV4cCI6MjA5MDM1MTE1M30.ai6oiGESIWk4dxIG_tFb8FOuTMEhNeaymE7eWLpTsnk"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

CACHE_TYPES = ["💚Traditional💚","🧡Multi🧡","💙Mystery💙","🩵Virtual🩵","🌍Earthcache🌍","📬Letterbox📬","🧭Wherigo🧭","❤️Event❤️","🪾CITO🪾"]
SIZES = ["micro","small","regular","large","other"]
ATTRIBUTES = ["👶děti👶","🐶psi🐶","🛠️speciální nástroj🛠️","🚗drive-in🚗","🔭vyhlídka🔭","🌞24/7🌞"]

# --- FUNKCE ---
def load_data():
    try:
        res = supabase.table("treasures").select("*").eq("user_id", st.session_state["username"]).execute()
        data = res.data or []
        if not data:
            res_templates = supabase.table("treasures").select("*").is_("user_id", "null").execute()
            templates = res_templates.data or []
            if templates:
                for t in templates:
                    new_t = t.copy()
                    if "id" in new_t: del new_t["id"]
                    new_t["user_id"] = st.session_state["username"]
                    supabase.table("treasures").insert(new_t).execute()
                res = supabase.table("treasures").select("*").eq("user_id", st.session_state["username"]).execute()
                data = res.data or []
        
        clean = []
        for t in data:
            clean.append({
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
        return clean
    except: return []

def save():
    try:
        supabase.table("treasures").delete().eq("user_id", st.session_state["username"]).execute()
        for t in st.session_state.treasures:
            t["user_id"] = st.session_state["username"]
            supabase.table("treasures").insert(t).execute()
        st.toast("Uloženo!", icon="💾")
    except Exception as e: st.error(f"Chyba: {e}")

# --- SESSION STATE ---
if "treasures" not in st.session_state:
    st.session_state.treasures = load_data()

for key, val in {"show_list": False, "open_detail": None, "open_detail_result": None, 
                 "edit_index": None, "results": [], "confirm_use": None, "confirm_delete": None}.items():
    if key not in st.session_state: st.session_state[key] = val

# --- SIDEBAR ---
with st.sidebar:
    st.write(f"Uživatel: **{st.session_state['username']}**")
    if st.button("Odhlásit se"):
        localS.removeItem("gc_user")
        st.session_state["username"] = None
        st.rerun()

# --- 1. ZADEJ KEŠ ---
st.title("Geocaching – výběr pokladů")
st.header("Zadej keš")

c_col1, c_col2 = st.columns(2)
cache_type = c_col1.selectbox("Typ keše", CACHE_TYPES)
cache_size = c_col2.selectbox("Velikost", SIZES)
cache_difficulty = st.slider("Obtížnost", 0.5, 5.0, 0.5, 0.5)
cache_terrain = st.slider("Terén", 0.5, 5.0, 0.5, 0.5)
cache_fav = st.number_input("Srdíčka", 0, 10000, 0)
cache_attrs = st.multiselect("Atributy keše", ATTRIBUTES)

if st.button("Vyhodnotit", use_container_width=True):
    results = []
    for i, t in enumerate(st.session_state.treasures):
        m = True
        if t["types"] and cache_type not in t["types"]: m = False
        if not (t["terrain_min"] <= cache_terrain <= t["terrain_max"]): m = False
        if not (t["difficulty_min"] <= cache_difficulty <= t["difficulty_max"]): m = False
        if t["sizes"] and cache_size not in t["sizes"]: m = False
        if cache_fav < t["fav_min"]: m = False
        if not set(t["attrs"]).issubset(set(cache_attrs)): m = False
        if m: results.append((i, t))
    st.session_state.results = sorted(results, key=lambda x: x[1]["remaining"])

# Výsledky
if st.session_state.results:
    st.subheader("Vhodné poklady:")
    for i, t in st.session_state.results:
        r_col1, r_col2, r_col3, r_col4 = st.columns([4,2,1,1])
        r_col1.write(t["name"])
        r_col2.write(f"Zbývá: {t['remaining']}")
        if r_col3.button("ℹ️", key=f"res_i_{i}"):
            st.session_state.open_detail_result = i if st.session_state.open_detail_result != i else None
        if r_col4.button("✅", key=f"use_{i}"):
            st.session_state.confirm_use = i
        
        if st.session_state.open_detail_result == i:
            st.info(f"T {t['terrain_min']}-{t['terrain_max']} | D {t['difficulty_min']}-{t['difficulty_max']} | FP {t['fav_min']}+")
        
        if st.session_state.confirm_use == i:
            if st.button(f"Potvrdit použití {t['name']}", key=f"y_{i}"):
                if st.session_state.treasures[i]["remaining"] > 0:
                    st.session_state.treasures[i]["remaining"] -= 1
                    save()
                st.session_state.confirm_use = None
                st.rerun()

# --- 2. SEZNAM POKLADŮ ---
st.divider()
if st.button("Zobrazit / skrýt seznam pokladů"):
    st.session_state.show_list = not st.session_state.show_list

if st.session_state.show_list:
    st.header("Seznam pokladů")
    for i, t in enumerate(st.session_state.treasures):
        l_col1, l_col2, l_col3 = st.columns([5,1,1])
        l_col1.write(f"**{t['name']}** ({t['remaining']}x)")
        if l_col2.button("✏️", key=f"edit_{i}"):
            st.session_state.edit_index = i
            st.rerun()
        if l_col3.button("🗑️", key=f"del_{i}"):
            st.session_state.treasures.pop(i)
            save()
            st.rerun()

# --- 3. FORMULÁŘ PŘIDAT / UPRAVIT ---
st.divider()
st.header("Přidat / upravit poklad")

# Výchozí hodnoty pro formulář
d = {"name": "", "types": [], "terrain_min": 0.5, "terrain_max": 5.0, "difficulty_min": 0.5, "difficulty_max": 5.0, "sizes": [], "fav_min": 0, "attrs": [], "remaining": 0}
if st.session_state.edit_index is not None:
    d = st.session_state.treasures[st.session_state.edit_index]

# Samotná pole formuláře
f_name = st.text_input("Název", value=d["name"])
f_types = st.multiselect("Typy keší", CACHE_TYPES, default=d["types"])
f_sizes = st.multiselect("Velikosti", SIZES, default=d["sizes"])
f_diff = st.slider("Obtížnost (min-max)", 0.5, 5.0, (d["difficulty_min"], d["difficulty_max"]), 0.5)
f_terr = st.slider("Terén (min-max)", 0.5, 5.0, (d["terrain_min"], d["terrain_max"]), 0.5)
f_fav = st.number_input("Min. srdíčka", 0, 1000, value=d["fav_min"])
f_attrs = st.multiselect("Atributy", ATTRIBUTES, default=d["attrs"])
f_rem = st.number_input("Zbývá kusů", 0, 100, value=d["remaining"])

b_col1, b_col2 = st.columns(2)
if b_col1.button("Uložit poklad", use_container_width=True, type="primary"):
    new_data = {
        "name": f_name, "types": f_types, "sizes": f_sizes,
        "difficulty_min": f_diff[0], "difficulty_max": f_diff[1],
        "terrain_min": f_terr[0], "terrain_max": f_terr[1],
        "fav_min": f_fav, "attrs": f_attrs, "remaining": f_rem
    }
    if st.session_state.edit_index is None:
        st.session_state.treasures.append(new_data)
    else:
        st.session_state.treasures[st.session_state.edit_index] = new_data
        st.session_state.edit_index = None
    save()
    st.rerun()

if b_col2.button("Zrušit / Reset", use_container_width=True):
    st.session_state.edit_index = None
    st.rerun()from supabase import create_client
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
