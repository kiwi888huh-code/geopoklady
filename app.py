import streamlit as st
import json
import os

st.title("Geocaching – výběr pokladů")

# ====== DATA ======
CACHE_TYPES = ["Traditional","Multi","Mystery","Virtual","Earthcache","Letterbox","Event","CITO","Wherigo"]
SIZES = ["micro","small","regular","large","other"]
ATTRIBUTES = ["děti","psi","speciální nástroj","drive-in","vyhlídka"]

FILE = "treasures.json"

# ====== NAČTENÍ ======
if "treasures" not in st.session_state:
    if os.path.exists(FILE):
        with open(FILE, "r", encoding="utf-8") as f:
            st.session_state.treasures = json.load(f)
    else:
        st.session_state.treasures = []

# ====== ULOŽENÍ FUNKCE ======
def save_data():
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.treasures, f, ensure_ascii=False, indent=2)

# ====== PŘIDAT POKLAD ======
st.header("Přidat poklad")

name = st.text_input("Název")
types = st.multiselect("Typy keší", CACHE_TYPES)

terrain_min = st.slider("Terén min", 0.5, 5.0, 1.0, 0.5)
terrain_max = st.slider("Terén max", 0.5, 5.0, 5.0, 0.5)

difficulty_min = st.slider("Obtížnost min", 0.5, 5.0, 1.0, 0.5)
difficulty_max = st.slider("Obtížnost max", 0.5, 5.0, 5.0, 0.5)

sizes = st.multiselect("Velikosti", SIZES)

fav_min = st.number_input("Minimální počet srdíček", 0, 10000, 0)

attrs = st.multiselect("Požadované atributy", ATTRIBUTES)

remaining = st.number_input("Zbývá keší", 0, 1000, 0)

if st.button("Přidat poklad"):
    st.session_state.treasures.append({
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
    })
    save_data()

# ====== SEZNAM ======
st.header("Seznam pokladů")

for i, t in enumerate(st.session_state.treasures):
    col1, col2, col3 = st.columns([4,2,1])

    col1.write(f"**{t['name']}**")
    col2.write(f"Zbývá: {t['remaining']}")

    if col3.button("❌", key=f"del_{i}"):
        st.session_state.treasures.pop(i)
        save_data()
        st.rerun()

# ====== CACHE ======
st.header("Zadej keš")

cache_type = st.selectbox("Typ keše", CACHE_TYPES)
cache_terrain = st.slider("Terén", 0.5, 5.0, 1.0, 0.5)
cache_difficulty = st.slider("Obtížnost", 0.5, 5.0, 1.0, 0.5)
cache_size = st.selectbox("Velikost", SIZES)
cache_fav = st.number_input("Počet srdíček", 0, 10000, 0)
cache_attrs = st.multiselect("Atributy keše", ATTRIBUTES)

# ====== MATCH ======
def matches(t, c):
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

    for attr in t["attrs"]:
        if attr not in c["attrs"]:
            return False

    return True

# ====== VYHODNOCENÍ ======
if st.button("Vyhodnotit"):
    cache = {
        "type": cache_type,
        "terrain": cache_terrain,
        "difficulty": cache_difficulty,
        "size": cache_size,
        "fav": cache_fav,
        "attrs": cache_attrs
    }

    valid = []

    for t in st.session_state.treasures:
        if matches(t, cache):
            valid.append((t["name"], t["remaining"]))

    st.subheader("Vhodné poklady:")

    if valid:
        for name, remaining in valid:
            st.write(f"✔ {name} (zbývá: {remaining})")
    else:
        st.write("Žádný poklad nesplňuje podmínky")
