import streamlit as st
import json
import os

# ====== STYL (šedé výběry) ======
st.markdown("""
<style>
div[data-baseweb="select"] > div {
    background-color: #2b2b2b !important;
    color: white !important;
}
ul {
    background-color: #2b2b2b !important;
    color: white !important;
}
span[data-baseweb="tag"] {
    background-color: #555 !important;
}
</style>
""", unsafe_allow_html=True)

st.title("Geocaching – výběr pokladů")

CACHE_TYPES = ["💚Traditional💚","🧡Multi🧡","💙Mystery💙","🩵Virtual🩵","🌍Earthcache🌍","📬Letterbox📬","🧭Wherigo🧭","❤️Event❤️","🪾CITO🪾"]
SIZES = ["micro","small","regular","large","other"]
ATTRIBUTES = ["👶děti👶","🐶psi🐶","🛠️speciální nástroj🛠️","🚗drive-in🚗","🔭vyhlídka🔭","🌞24/7🌞"]

# ====== MAPOVÁNÍ STARÝCH DAT ======
TYPE_MAP = {
    "Traditional": "💚Traditional💚",
    "Multi": "🧡Multi🧡",
    "Mystery": "💙Mystery💙",
    "Virtual": "🩵Virtual🩵",
    "Earthcache": "🌍Earthcache🌍",
    "Letterbox": "📬Letterbox📬",
    "Wherigo": "🧭Wherigo🧭",
    "Event": "❤️Event❤️",
    "CITO": "🪾CITO🪾"
}

ATTRIBUTE_MAP = {
    "děti": "👶děti👶",
    "psi": "🐶psi🐶",
    "speciální nástroj": "🛠️speciální nástroj🛠️",
    "drive-in": "🚗drive-in🚗",
    "vyhlídka": "🔭vyhlídka🔭",
    "24/7": "🌞24/7🌞"
}

# ====== LOAD ======
if "treasures" not in st.session_state:
    if os.path.exists("poklady.json"):
        try:
            with open("poklady.json", "r") as f:
                st.session_state.treasures = json.load(f)
        except:
            st.session_state.treasures = []
    else:
        st.session_state.treasures = []

# ====== OPRAVA STARÝCH DAT ======
for t in st.session_state.treasures:
    t.setdefault("remaining", 0)
    t.setdefault("types", [])
    t.setdefault("sizes", [])
    t.setdefault("attrs", [])

    # převod typů
    t["types"] = [TYPE_MAP.get(x, x) for x in t["types"]]

    # převod atributů
    t["attrs"] = [ATTRIBUTE_MAP.get(x, x) for x in t["attrs"]]

if "form_id" not in st.session_state:
    st.session_state.form_id = 0

if "open_detail" not in st.session_state:
    st.session_state.open_detail = None

if "edit_index" not in st.session_state:
    st.session_state.edit_index = None

# ====== FORM ======
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
    t = st.session_state.treasures[st.session_state.edit_index]
    default = {
        "name": t.get("name", ""),
        "types": t.get("types", []),
        "terrain_min": t.get("terrain_min", 0.5),
        "terrain_max": t.get("terrain_max", 5.0),
        "difficulty_min": t.get("difficulty_min", 0.5),
        "difficulty_max": t.get("difficulty_max", 5.0),
        "sizes": t.get("sizes", []),
        "fav_min": t.get("fav_min", 0),
        "attrs": t.get("attrs", []),
        "remaining": t.get("remaining", 0)
    }

form_key = f"form_{st.session_state.form_id}"

with st.form(form_key):
    name = st.text_input("Název pokladu", value=default["name"])

    safe_types = [x for x in default["types"] if x in CACHE_TYPES]
    types = st.multiselect("Typy keší", CACHE_TYPES, default=safe_types)

    terrain_min = st.slider("Terén min", 0.5, 5.0, default["terrain_min"], 0.5)
    terrain_max = st.slider("Terén max", 0.5, 5.0, default["terrain_max"], 0.5)

    difficulty_min = st.slider("Obtížnost min", 0.5, 5.0, default["difficulty_min"], 0.5)
    difficulty_max = st.slider("Obtížnost max", 0.5, 5.0, default["difficulty_max"], 0.5)

    safe_sizes = [x for x in default["sizes"] if x in SIZES]
    sizes = st.multiselect("Velikosti", SIZES, default=safe_sizes)

    fav_min = st.number_input("Minimální srdíčka", 0, 10000, default["fav_min"])

    safe_attrs = [x for x in default["attrs"] if x in ATTRIBUTES]
    attrs = st.multiselect("Atributy", ATTRIBUTES, default=safe_attrs)

    remaining = st.number_input("Zbývá keší", 0, 1000, default["remaining"])

    submitted = st.form_submit_button("Uložit")

if submitted:
    if name.strip():
        new_data = {
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
            st.session_state.treasures.append(new_data)
        else:
            st.session_state.treasures[st.session_state.edit_index] = new_data
            st.session_state.edit_index = None

        with open("poklady.json", "w") as f:
            json.dump(st.session_state.treasures, f)

        st.session_state.form_id += 1
        st.rerun()

# ====== LIST ======
st.header("Seznam pokladů")

for i, t in enumerate(st.session_state.treasures):
    col1, col2, col3, col4, col5 = st.columns([4,2,1,1,1])

    col1.write(f"• {t['name']}")
    col2.write(f"Zbývá: {t['remaining']}")

    if col3.button("ℹ️", key=f"info_{i}"):
        st.session_state.open_detail = i if st.session_state.open_detail != i else None

    if col4.button("✏️", key=f"edit_{i}"):
        st.session_state.edit_index = i
        st.session_state.form_id += 1
        st.rerun()

    if col5.button("❌", key=f"delete_{i}"):
        st.session_state.treasures.pop(i)
        with open("poklady.json", "w") as f:
            json.dump(st.session_state.treasures, f)
        st.session_state.open_detail = None
        st.rerun()

    if st.session_state.open_detail == i:
        st.markdown(f"""
**Typy:** {t['types']}  
**Terén:** {t['terrain_min']} – {t['terrain_max']}  
**Obtížnost:** {t['difficulty_min']} – {t['difficulty_max']}  
**Velikosti:** {t['sizes']}  
**Min. srdíčka:** {t['fav_min']}  
**Atributy:** {t['attrs']}  
**Zbývá:** {t['remaining']}
""")

# ====== CACHE ======
st.header("Zadej keš")

cache_type = st.selectbox("Typ keše", CACHE_TYPES)
cache_terrain = st.slider("Terén", 0.5, 5.0, 0.5, 0.5)
cache_difficulty = st.slider("Obtížnost", 0.5, 5.0, 0.5, 0.5)
cache_size = st.selectbox("Velikost", SIZES)
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

    result = [(t["name"], t["remaining"]) for t in st.session_state.treasures if match(t, cache)]

    st.subheader("Vhodné poklady:")

    if result:
        for name, remaining in result:
            st.write(f"✔ {name} (zbývá: {remaining})")
    else:
        st.write("Žádný poklad nesplňuje podmínky")
