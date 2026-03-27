import streamlit as st
import json
import os

st.title("Geocaching – výběr pokladů")

CACHE_TYPES = ["Traditional","Multi","Mystery","Virtual","Earthcache","Letterbox","Event","CITO","Wherigo"]
SIZES = ["micro","small","regular","large","other"]
ATTRIBUTES = ["děti","psi","speciální nástroj","drive-in","vyhlídka"]

if "treasures" not in st.session_state:
    if os.path.exists("poklady.json"):
        try:
            with open("poklady.json", "r") as f:
                st.session_state.treasures = json.load(f)
        except:
            st.session_state.treasures = []
    else:
        st.session_state.treasures = []

st.header("Přidat poklad")

name = st.text_input("Název pokladu")
types = st.multiselect("Typy keší", CACHE_TYPES)

terrain_min = st.slider("Terén min", 0.5, 5.0, 1.0, 0.5)
terrain_max = st.slider("Terén max", 0.5, 5.0, 5.0, 0.5)

difficulty_min = st.slider("Obtížnost min", 0.5, 5.0, 1.0, 0.5)
difficulty_max = st.slider("Obtížnost max", 0.5, 5.0, 5.0, 0.5)

sizes = st.multiselect("Velikosti", SIZES)
fav_min = st.number_input("Minimální srdíčka", 0, 10000, 0)
attrs = st.multiselect("Atributy (musí být stejné)", ATTRIBUTES)

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

        st.success("Uloženo")

st.header("Seznam pokladů")

for i, t in enumerate(st.session_state.treasures):
    col1, col2 = st.columns([4,1])
    col1.write("• " + t["name"])
    if col2.button("❌", key=i):
        st.session_state.treasures.pop(i)
        with open("poklady.json", "w") as f:
            json.dump(st.session_state.treasures, f)
        st.experimental_rerun()

st.header("Zadej keš")

cache_type = st.selectbox("Typ", CACHE_TYPES)
cache_terrain = st.slider("Terén", 0.5, 5.0, 1.0, 0.5)
cache_difficulty = st.slider("Obtížnost", 0.5, 5.0, 1.0, 0.5)
cache_size = st.selectbox("Velikost", SIZES)
cache_fav = st.number_input("Srdíčka", 0, 10000, 0)
cache_attrs = st.multiselect("Atributy", ATTRIBUTES)

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
    if set(t["attrs"]) != set(c["attrs"]):
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

    vysledek = []

    for t in st.session_state.treasures:
        if match(t, cache):
            vysledek.append(t["name"])

    if vysledek:
        for v in vysledek:
            st.write("✔", v)
    else:
        st.write("Žádný poklad nesplňuje podmínky")
