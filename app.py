from supabase import create_client
import streamlit as st

# --- JEDNODUCHÉ PŘIHLÁŠENÍ ---
if "username" not in st.session_state:
    st.session_state["username"] = None

if st.session_state["username"] is None:
    st.title("Geocaching filtr – Přihlášení")
    # Použijeme text_input, ale uložíme ho do session_state
    user_input = st.text_input("Zadej svou přezdívku (nemusí být oficiální):").lower().strip()
    if st.button("Vstoupit"):
        if user_input:
            st.session_state["username"] = user_input
            st.rerun()
        else:
            st.error("Jméno nesmí být prázdné!")
    st.stop() # Zastaví zbytek aplikace, dokud není username

SUPABASE_URL = "https://ycwkedvzyhsofbuhludk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inljd2tlZHZ6eWhzb2ZidWhsdWRrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3NzUxNTMsImV4cCI6MjA5MDM1MTE1M30.ai6oiGESIWk4dxIG_tFb8FOuTMEhNeaymE7eWLpTsnk"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("Geocaching – výběr pokladů")

CACHE_TYPES = ["💚Traditional💚","🧡Multi🧡","💙Mystery💙","🩵Virtual🩵","🌍Earthcache🌍","📬Letterbox📬","🧭Wherigo🧭","❤️Event❤️","🪾CITO🪾"]
SIZES = ["micro","small","regular","large","other"]
ATTRIBUTES = ["👶děti👶","🐶psi🐶","🛠️speciální nástroj🛠️","🚗drive-in🚗","🔭vyhlídka🔭","🌞24/7🌞"]

# ===== LOAD =====
def load_data():
    try:
       # Načte jen poklady, které patří přihlášenému uživateli
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
                    "remaining": max(0, int(t.get("remaining") or 0))  # 🔥 nikdy záporné
                })
            except:
                # když je jeden poklad rozbitý → přeskoč ho
                continue

        return clean_data

    except Exception as e:
        st.error(f"Chyba při načítání databáze: {e}")
        return []


# ===== INIT SESSION =====
if "treasures" not in st.session_state:
    st.session_state.treasures = []

data = load_data()
if isinstance(data, list):
    st.session_state.treasures = data
# ===== STAVY =====
for key, default in {
    "show_list": False,   # 🔴 defaultně skrytý
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
        # Smaže jen tvoje poklady, ne cizí!
        supabase.table("treasures").delete().eq("user_id", st.session_state["username"]).execute()
        
        for t in st.session_state.treasures:
            # Každému pokladu přidáme tvoje jméno před uložením
            t["user_id"] = st.session_state["username"]
            supabase.table("treasures").insert(t).execute()
        st.toast("Uloženo do databáze!", icon="💾")
    except Exception as e:
        st.error(f"Chyba při ukládání: {e}")

# ===== DETAIL =====
def show_detail(t):
    st.markdown(f"""
**Typy:** {", ".join(t['types']) if t['types'] else "—"}  
**Terén:** {t['terrain_min']} – {t['terrain_max']}  
**Obtížnost:** {t['difficulty_min']} – {t['difficulty_max']}  
**Velikosti:** {", ".join(t['sizes']) if t['sizes'] else "—"}  
**Min. srdíčka:** {t['fav_min']}  
**Atributy:** {", ".join(t['attrs']) if t['attrs'] else "—"}  
**Zbývá:** {t['remaining']}
""")

# =====================================================
# 🔥 1. KEŠ NAHORU
# =====================================================

st.header("Zadej keš")

cache_type = st.selectbox("Typ keše", CACHE_TYPES)
cache_size = st.selectbox("Velikost", SIZES)
cache_difficulty = st.slider("Obtížnost", 0.5, 5.0, 0.5, 0.5)
cache_terrain = st.slider("Terén", 0.5, 5.0, 0.5, 0.5)
cache_fav = st.number_input("Srdíčka", 0, 10000, 0)
cache_attrs = st.multiselect("Atributy keše", ATTRIBUTES)

def match(t, c):
    if t["types"] and c["type"] not in t["types"]:
        return False
    if not (t["terrain_min"] <= c["terrain"] <= t["terrain_max"]):
        return False
    if not (t["difficulty_min"] <= c["difficulty"] <= t["difficulty_max"]):
        return False
    if t["sizes"] and c["size"] not in t["sizes"]:
        return False
    if c["fav"] < t["fav_min"]:
        return False
    if not set(t["attrs"]).issubset(set(c["attrs"])):
        return False
    return True

if st.button("Vyhodnotit"):
    cache = {
        "type": cache_type,
        "terrain": cache_terrain,
        "difficulty": cache_difficulty,
        "size": cache_size,
        "fav": cache_fav,
        "attrs": cache_attrs
    }

    results = [(i, t) for i, t in enumerate(st.session_state.treasures) if match(t, cache)]
    st.session_state.results = sorted(results, key=lambda x: (x[1]["remaining"], x[1]["name"]))

# ===== VÝSLEDKY =====
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
            show_detail(t)

        if st.session_state.confirm_use == i:
            st.warning(f"Opravdu použít '{t['name']}'?")
            c1, c2 = st.columns(2)

            if c1.button("Ano", key=f"use_yes_{i}"):
                if st.session_state.treasures[i]["remaining"] > 0:
                    st.session_state.treasures[i]["remaining"] -= 1
                    save()
                st.session_state.confirm_use = None
                st.rerun()

            if c2.button("Ne", key=f"use_no_{i}"):
                st.session_state.confirm_use = None
else:
    st.write("Žádný poklad nesplňuje podmínky")

# =====================================================
# 🔥 2. SEZNAM (SKRYTÝ)
# =====================================================

if st.button("Zobrazit / skrýt seznam pokladů"):
    st.session_state.show_list = not st.session_state.show_list

if st.session_state.show_list:
    st.header("Seznam pokladů")

    # Seskupíme všechno podle jména pro přehlednost
    grouped_all = {}
    for i, t in enumerate(st.session_state.treasures):
        name = t["name"]
        if name not in grouped_all:
            grouped_all[name] = {"remaining": t["remaining"], "indices": []}
        grouped_all[name]["indices"].append(i)

    # Seřadíme abecedně
    for name in sorted(grouped_all.keys()):
        info = grouped_all[name]
        col1, col2, col3, col4, col5 = st.columns([4,2,1,1,1])

        col1.write(f"**{name}** ({len(info['indices'])} varianty)")
        col2.write(info["remaining"])

        if col3.button("ℹ️", key=f"list_info_{name}"):
            st.session_state.open_detail = name if st.session_state.open_detail != name else None

        if col4.button("✏️", key=f"list_edit_{name}"):
            # Editace vždy první varianty (pro jednoduchost)
            st.session_state.edit_index = info["indices"][0]
            st.rerun()

        if col5.button("❌", key=f"list_del_{name}"):
            st.session_state.confirm_delete = name

        if st.session_state.open_detail == name:
            for idx in info["indices"]:
                show_detail(st.session_state.treasures[idx])
                st.divider()

        if st.session_state.confirm_delete == name:
            st.warning(f"Smazat VŠECHNY varianty '{name}'?")
            c1, c2 = st.columns(2)

            if c1.button("Ano", key=f"del_yes_{name}"):
                # Necháme jen ty, co se nejmenují stejně
                st.session_state.treasures = [t for t in st.session_state.treasures if t["name"] != name]
                st.session_state.confirm_delete = None
                save()
                st.rerun()

            if c2.button("Ne", key=f"del_no_{name}"):
                st.session_state.confirm_delete = None

# =====================================================
# 🔥 3. FORM DOLE
# =====================================================

st.header("Přidat / upravit poklad")

default = {
    "name": "",
    "types": [],
    "terrain_min": 0.5,
    "terrain_max": 5.0,
    "difficulty_min": 0.5,
    "difficulty_max": 5.0,
    "sizes": [],
    "fav_min": 0,
    "attrs": [],
    "remaining": 0
}

if st.session_state.edit_index is not None:
    default = st.session_state.treasures[st.session_state.edit_index]

name = st.text_input("Název", value=default["name"])
types = st.multiselect("Typy keší", CACHE_TYPES, default=default["types"])
sizes = st.multiselect("Velikosti", SIZES, default=default["sizes"])

difficulty_min = st.slider("Obtížnost min", 0.5, 5.0, default["difficulty_min"], 0.5)
difficulty_max = st.slider("Obtížnost max", 0.5, 5.0, default["difficulty_max"], 0.5)

terrain_min = st.slider("Terén min", 0.5, 5.0, default["terrain_min"], 0.5)
terrain_max = st.slider("Terén max", 0.5, 5.0, default["terrain_max"], 0.5)

fav_min = st.number_input("Minimální srdíčka", 0, 10000, default["fav_min"])
attrs = st.multiselect("Atributy", ATTRIBUTES, default=default["attrs"])
remaining = st.number_input("Zbývá keší", 0, 1000, default["remaining"])

if st.button("Uložit poklad"):
    data = {
        "name": name,
        "types": types,
        "terrain_min": terrain_min,
        "terrain_max": terrain_max,
        "difficulty_min": difficulty_min,
        "difficulty_max": difficulty_max,
        "sizes": sizes,
        "fav_min": fav_min,
        "attrs": attrs,
        "remaining": remaining
    }

    if st.session_state.edit_index is None:
        st.session_state.treasures.append(data)
    else:
        st.session_state.treasures[st.session_state.edit_index] = data
        st.session_state.edit_index = None

    save()
    st.rerun()
