import streamlit as st

st.title("Geocaching – výběr pokladů")

# ====== DATA ======
CACHE_TYPES = ["Traditional","Multi","Mystery","Virtual","Earthcache","Letterbox","Event","CITO","Wherigo"]
SIZES = ["micro","small","regular","large","other"]
ATTRIBUTES = ["děti","psi","speciální nástroj","drive-in","vyhlídka"]

if "treasures" not in st.session_state:
    st.session_state.treasures = []

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
        "attrs": attrs
    })

# ====== SEZNAM ======
st.header("Seznam pokladů")
for t in st.session_state.treasures:
    st.write("•", t["name"])

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
            valid.append(t["name"])

    st.subheader("Vhodné poklady:")

    if valid:
        for v in valid:
            st.write("✔", v)
    else:
        st.write("Žádný poklad nesplňuje podmínky")import streamlit as st

st.title("Geocaching – výběr pokladů")

if "treasures" not in st.session_state:
    st.session_state.treasures = []

st.header("Přidat poklad")

name = st.text_input("Název pokladu")
difficulty_min = st.number_input("Minimální obtížnost", 1.0, 5.0, 1.0)
terrain_min = st.number_input("Minimální terén", 1.0, 5.0, 1.0)
cache_type = st.selectbox("Typ keše", ["any", "traditional", "mystery", "multi"])
size_not = st.selectbox("Zakázaná velikost", ["none", "micro", "small", "regular", "large"])

if st.button("Přidat poklad"):
    st.session_state.treasures.append({
        "name": name,
        "difficulty_min": difficulty_min,
        "terrain_min": terrain_min,
        "type": cache_type,
        "size_not": size_not
    })

st.header("Seznam pokladů")
for t in st.session_state.treasures:
    st.write(t["name"])

st.header("Zadej keš")

cache_difficulty = st.number_input("Obtížnost keše", 1.0, 5.0, 1.0, key="cd")
cache_terrain = st.number_input("Terén keše", 1.0, 5.0, 1.0, key="ct")
cache_type_input = st.selectbox("Typ keše", ["traditional", "mystery", "multi"], key="ctype")
cache_size = st.selectbox("Velikost", ["micro", "small", "regular", "large"])

def matches(t, c):
    if c["difficulty"] < t["difficulty_min"]:
        return False
    if c["terrain"] < t["terrain_min"]:
        return False
    if t["type"] != "any" and c["type"] != t["type"]:
        return False
    if t["size_not"] != "none" and c["size"] == t["size_not"]:
        return False
    return True

if st.button("Vyhodnotit"):
    cache = {
        "difficulty": cache_difficulty,
        "terrain": cache_terrain,
        "type": cache_type_input,
        "size": cache_size
    }

    valid = []
    for t in st.session_state.treasures:
        if matches(t, cache):
            valid.append(t["name"])

    st.subheader("Vhodné poklady:")
    if valid:
        for v in valid:
            st.write("✔", v)
    else:
        st.write("Žádný poklad nesplňuje podmínky")
