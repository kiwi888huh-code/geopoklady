import streamlit as st
import json
import os

st.title("Geocaching – výběr pokladů")

CACHE_TYPES = ["Traditional","Multi","Mystery","Virtual","Earthcache","Letterbox","Event","CITO","Wherigo"]
SIZES = ["micro","small","regular","large","other"]
ATTRIBUTES = ["děti","psi","speciální nástroj","drive-in","vyhlídka","24/7"]

# ====== DEFAULTY ======
def reset_form():
    # poklad
    st.session_state.t_name = ""
    st.session_state.t_types = CACHE_TYPES.copy()
    st.session_state.t_terrain_min = 0.5
    st.session_state.t_terrain_max = 5.0
    st.session_state.t_diff_min = 0.5
    st.session_state.t_diff_max = 5.0
    st.session_state.t_sizes = SIZES.copy()
    st.session_state.t_fav = 0
    st.session_state.t_attrs = []

    # cache
    st.session_state.c_type = CACHE_TYPES[0]
    st.session_state.c_terrain = 0.5
    st.session_state.c_diff = 0.5
    st.session_state.c_size = SIZES[0]
    st.session_state.c_fav = 0
    st.session_state.c_attrs = []

# inicializace defaultů (jen při prvním spuštění)
if "t_name" not in st.session_state:
    reset_form()

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

if "open_detail" not in st.session_state:
    st.session_state.open_detail = None

if "edit_index" not in st.session_state:
    st.session_state.edit_index = None

# ====== FORM ======
st.header("Přidat / upravit poklad")

name = st.text_input("Název pokladu", key="t_name")
types = st.multiselect("Typy keší", CACHE_TYPES, key="t_types")

terrain_min = st.slider("Terén min", 0.5, 5.0, key="t_terrain_min", step=0.5)
terrain_max = st.slider("Terén max", 0.5, 5.0, key="t_terrain_max", step=0.5)

difficulty_min = st.slider("Obtížnost min", 0.5, 5.0, key="t_diff_min", step=0.5)
difficulty_max = st.slider("Obtížnost max", 0.5, 5.0, key="t_diff_max", step=0.5)

sizes = st.multiselect("Velikosti", SIZES, key="t_sizes")
fav_min = st.number_input("Minimální srdíčka", 0, 10000, key="t_fav")
attrs = st.multiselect("Atributy", ATTRIBUTES, key="t_attrs")

# ====== SAVE / EDIT ======
if st.session_state.edit_index is None:
    if st.button("Přidat poklad"):
        if name.strip() != "":
            st.session_state.treasures.append({
                "name": name,
                "types": types,
                "terrain_min": terrain_min,
                "terrain_max": terrain_max,
                "difficulty_min": difficulty_min,
                "difficulty_max": difficulty_max,
                "sizes": sizes,
                "fav_min": fav_min,
                "attrs": attrs
            })

            with open("poklady.json", "w") as f:
                json.dump(st.session_state.treasures, f)

            reset_form()
            st.rerun()
else:
    if st.button("Uložit změny"):
        st.session_state.treasures[st.session_state.edit_index] = {
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

        with open("poklady.json", "w") as f:
            json.dump(st.session_state.treasures, f)

        st.session_state.edit_index = None
        reset_form()
        st.rerun()

# ====== LIST ======
st.header("Seznam pokladů")

for i, t in enumerate(st.session_state.treasures):
    col1, col2, col3, col4 = st.columns([4,1,1,1])

    col1.write(f"• {t['name']}")

    if col2.button("ℹ️", key=f"info_{i}"):
        st.session_state.open_detail = i if st.session_state.open_detail != i else None

    if col3.button("✏️", key=f"edit_{i}"):
        st.session_state.edit_index = i

        # naplnění formuláře
        st.session_state.t_name = t["name"]
        st.session_state.t_types = t["types"]
        st.session_state.t_terrain_min = t["terrain_min"]
        st.session_state.t_terrain_max = t["terrain_max"]
        st.session_state.t_diff_min = t["difficulty_min"]
        st.session_state.t_diff_max = t["difficulty_max"]
        st.session_state.t_sizes = t["sizes"]
        st.session_state.t_fav = t["fav_min"]
        st.session_state.t_attrs = t["attrs"]

        st.rerun()

    if col4.button("❌", key=f"delete_{i}"):
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
""")

# ====== CACHE ======
st.header("Zadej keš")

cache_type = st.selectbox("Typ keše", CACHE_TYPES, key="c_type")
cache_terrain = st.slider("Terén", 0.5, 5.0, key="c_terrain", step=0.5)
cache_difficulty = st.slider("Obtížnost", 0.5, 5.0, key="c_diff", step=0.5)
cache_size = st.selectbox("Velikost", SIZES, key="c_size")
cache_fav = st.number_input("Srdíčka", 0, 10000, key="c_fav")
cache_attrs = st.multiselect("Atributy keše", ATTRIBUTES, key="c_attrs")

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

    result = [t["name"] for t in st.session_state.treasures if match(t, cache)]

    st.subheader("Vhodné poklady:")

    if result:
        for r in result:
            st.write("✔", r)
    else:
        st.write("Žádný poklad nesplňuje podmínky")
