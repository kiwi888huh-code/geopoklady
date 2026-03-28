import streamlit as st
import json
import os

st.title("Geocaching – výběr pokladů")

CACHE_TYPES = ["💚Traditional💚","🧡Multi🧡","💙Mystery💙","🩵Virtual🩵","🌍Earthcache🌍","📬Letterbox📬","🧭Wherigo🧭","❤️Event❤️","🪾CITO🪾"]
SIZES = ["micro","small","regular","large","other"]
ATTRIBUTES = ["👶děti👶","🐶psi🐶","🛠️speciální nástroj🛠️","🚗drive-in🚗","🔭vyhlídka🔭","🌞24/7🌞"]

FILE = "poklady.json"

# ===== LOAD =====
if "treasures" not in st.session_state:
    if os.path.exists(FILE):
        with open(FILE, "r") as f:
            st.session_state.treasures = json.load(f)
    else:
        st.session_state.treasures = []

# ===== STAVY =====
for key, default in {
    "show_list": True,
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
    with open(FILE, "w") as f:
        json.dump(st.session_state.treasures, f)

# ===== DETAIL FUNKCE =====
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

# ===== FORM =====
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

if st.button("Uložit"):
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

# ===== TOGGLE =====
if st.button("Zobrazit / skrýt seznam"):
    st.session_state.show_list = not st.session_state.show_list

# ===== SEZNAM =====
if st.session_state.show_list:
    st.header("Seznam pokladů")

    sorted_treasures = sorted(
        list(enumerate(st.session_state.treasures)),
        key=lambda x: (x[1]["remaining"], x[1]["name"])
    )

    for i, t in sorted_treasures:
        col1, col2, col3, col4, col5 = st.columns([4,2,1,1,1])

        col1.write(t["name"])
        col2.write(t["remaining"])

        if col3.button("ℹ️", key=f"info_{i}"):
            st.session_state.open_detail = i if st.session_state.open_detail != i else None

        if col4.button("✏️", key=f"edit_{i}"):
            st.session_state.edit_index = i
            st.rerun()

        if col5.button("❌", key=f"del_{i}"):
            st.session_state.confirm_delete = i

        if st.session_state.open_detail == i:
            show_detail(t)

        # potvrzení smazání
        if st.session_state.confirm_delete == i:
            st.warning(f"Opravdu smazat '{t['name']}'?")
            c1, c2 = st.columns(2)

            if c1.button("Ano", key=f"del_yes_{i}"):
                st.session_state.treasures.pop(i)
                st.session_state.confirm_delete = None
                save()
                st.rerun()

            if c2.button("Ne", key=f"del_no_{i}"):
                st.session_state.confirm_delete = None

# ===== CACHE =====
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

# ===== VYHODNOCENÍ =====
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

# ===== VÝPIS =====
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

        # potvrzení použití
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
