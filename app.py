import streamlit as st
import json
import os

# ====== STYL ======
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

# ====== LOAD ======
if "treasures" not in st.session_state:
    if os.path.exists("poklady.json"):
        with open("poklady.json", "r") as f:
            st.session_state.treasures = json.load(f)
    else:
        st.session_state.treasures = []

# ====== STAVY ======
if "show_list" not in st.session_state:
    st.session_state.show_list = True

if "open_detail" not in st.session_state:
    st.session_state.open_detail = None

if "open_detail_result" not in st.session_state:
    st.session_state.open_detail_result = None

# ====== FORM ======
st.header("Přidat poklad")

name = st.text_input("Název")
types = st.multiselect("Typy keší", CACHE_TYPES)
sizes = st.multiselect("Velikosti", SIZES)

difficulty_min = st.slider("Obtížnost min", 0.5, 5.0, 0.5, 0.5)
difficulty_max = st.slider("Obtížnost max", 0.5, 5.0, 5.0, 0.5)

terrain_min = st.slider("Terén min", 0.5, 5.0, 0.5, 0.5)
terrain_max = st.slider("Terén max", 0.5, 5.0, 5.0, 0.5)

fav_min = st.number_input("Minimální srdíčka", 0, 10000, 0)
attrs = st.multiselect("Atributy", ATTRIBUTES)
remaining = st.number_input("Zbývá keší", 0, 1000, 0)

if st.button("Přidat"):
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
    with open("poklady.json", "w") as f:
        json.dump(st.session_state.treasures, f)
    st.rerun()

# ====== TOGGLE SEZNAM ======
if st.button("Zobrazit / skrýt seznam"):
    st.session_state.show_list = not st.session_state.show_list

# ====== SEZNAM ======
if st.session_state.show_list:
    st.header("Seznam pokladů")

    sorted_treasures = sorted(st.session_state.treasures, key=lambda x: x["remaining"])

    for i, t in enumerate(sorted_treasures):
        col1, col2, col3 = st.columns([5,2,1])

        col1.write(f"{t['name']}")
        col2.write(f"{t['remaining']}")

        if col3.button("ℹ️", key=f"info_{i}"):
            st.session_state.open_detail = i if st.session_state.open_detail != i else None

        if st.session_state.open_detail == i:
            st.write(t)

# ====== CACHE ======
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

# ====== VÝSLEDKY ======
if st.button("Vyhodnotit"):
    cache = {
        "type": cache_type,
        "terrain": cache_terrain,
        "difficulty": cache_difficulty,
        "size": cache_size,
        "fav": cache_fav,
        "attrs": cache_attrs
    }

    results = [t for t in st.session_state.treasures if match(t, cache)]
    results = sorted(results, key=lambda x: x["remaining"])

    st.subheader("Vhodné poklady:")

    if results:
        for i, t in enumerate(results):
            col1, col2, col3 = st.columns([5,2,1])

            col1.write(f"{t['name']}")
            col2.write(f"{t['remaining']}")

            if col3.button("ℹ️", key=f"res_{i}"):
                st.session_state.open_detail_result = i if st.session_state.open_detail_result != i else None

            if st.session_state.open_detail_result == i:
                st.write(t)

    else:
        st.write("Žádný poklad nesplňuje podmínky")
