import streamlit as st

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
