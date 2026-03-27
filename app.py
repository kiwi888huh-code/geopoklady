import streamlit as st
import json
import os

st.title("Geocaching – výběr pokladů")

CACHE_TYPES = ["Traditional","Multi","Mystery","Virtual","Earthcache","Letterbox","Event","CITO","Wherigo"]
SIZES = ["micro","small","regular","large","other"]
ATTRIBUTES = ["děti","psi","speciální nástroj","drive-in","vyhlídka"]

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

# stav pro rozbalení detailu
if "open_detail" not in st.session_state:
    st.session_state.open_detail = None

# ====== ADD TREASURE ======
st.header("Přidat poklad")

name = st.text_input("Název pokladu")
types = st.multiselect("Typy keší", CACHE_TYPES)

terrain_min = st.slider("Terén min", 0.5, 5.0, 1.0, 0.5)
terrain_max = st.slider("Terén max", 0.5, 5.0, 5.0, 0.5)

difficulty_min = st.slider("Obtížnost min", 0.5, 5.0, 1.0, 0.5)
difficulty_max = st.slider("Obtížnost max", 0.5, 5.0, 5.0, 0.5)

sizes = st.multiselect("Velikosti", SIZES)
fav_min = st.number_input("Minimální srdíčka", 0, 10000, 0)
attrs = st.multiselect("Požadované atributy", ATTRIBUTES)

if st.button("Přidat poklad"):
    if name.strip() != "":
        new = {
            "name": name,
            "types": types,
            "terrain_min": terrain_min,
            "terrain_max": terrain_max,
            "difficulty_min": difficulty_min,
            "difficulty_max": difficulty_max,
            "sizes": sizes,
            "fav_min": fav_min,
            "attrs": attrs
        }

        st.session_state.treasures.append(new)

        with open("poklady.json", "w") as f:
            json.dump(st.session_state.treasures, f)

        st.success("Poklad uložen")
    else:
        st.warning("Zadej název")

# ====== LIST + DELETE + DETAIL ======
st.header("Seznam pokladů")

if st.session_state.treasures:
    for i, t in enumerate(st.session_state.treasures):
        col1, col2, col3 = st.columns([4,1,1])

        col1.write(f"• {t['name']}")

        # INFO tlačítko (toggle)
        if col2.button("ℹ️", key=f"info_{i}"):
            if st.session_state.open_detail == i:
                st.session_state.open_detail = None
            else:
                st.session_state.open_detail = i

        # DELETE tlačítko
        if col3.button("❌", key=f"delete_{i}"):
            st.session_state.treasures.pop(i)

            with open("poklady.json", "w") as f:
                json.dump(st.session_state.treasures, f)

            st.session_state.open_detail = None
            st.rerun()

        # DETAIL (zobrazení)
        if st.session_state.open_detail == i:
            st.markdown(f"""
**Typy:** {t['types']}  
**Terén:** {t['terrain_min']} – {t['terrain_max']}  
**Obtížnost:** {t['difficulty_min']} – {t['difficulty_max']}  
**Velikosti:** {t['sizes']}  
**Min. srdíčka:** {t['fav_min']}  
**Atributy:** {t['attrs']}
""")
else:
    st.write("Žádné poklady")

# ====== CACHE INPUT ======
st.header("Zadej keš")

cache_type = st.selectbox("Typ keše", CACHE_TYPES)
cache_terrain = st.slider("Terén", 0.5, 5.0, 1.0, 0.5)
cache_difficulty = st.slider("Obtížnost", 0.5, 5.0, 1.0, 0.5)
cache_size = st.selectbox("Velikost", SIZES)
cache_fav = st.number_input("Srdíčka", 0, 10000, 0)
cache_attrs = st.multiselect("Atributy keše", ATTRIBUTES)

# ====== MATCH ======
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

    # atributy = podmnožina
    if not set(t["attrs"]).issubset(set(c["attrs"])):
        return False

    return True

# ====== EVALUATE ======
if st.button("Vyhodnotit"):
    cache = {
        "type": cache_type,
        "terrain": cache_terrain,
        "difficulty": cache_difficulty,
        "size": cache_size,
        "fav": cache_fav,
        "attrs": cache_attrs
    }

    result = []

    for t in st.session_state.treasures:
        if match(t, cache):
            result.append(t["name"])

    st.subheader("Vhodné poklady:")

    if result:
        for r in result:
            st.write("✔", r)
    else:
        st.write("Žádný poklad nesplňuje podmínky")
