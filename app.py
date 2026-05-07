from supabase import create_client
import streamlit as st
from streamlit_local_storage import LocalStorage

# --- INICIALIZACE ---
localS = LocalStorage()

if "username" not in st.session_state:
    st.session_state["username"] = None

# --- LOGIKA PŘIHLÁŠENÍ S PAMĚTÍ ---
if st.session_state["username"] is None:
    stored_user = localS.getItem("gc_user")
    if stored_user:
        st.session_state["username"] = stored_user

url_params = st.query_params
if "user" in url_params and st.session_state["username"] is None:
    user_val = url_params["user"].lower().strip()
    st.session_state["username"] = user_val
    localS.setItem("gc_user", user_val)

if st.session_state["username"] is None:
    st.title("Geocaching filtr – Přihlášení")
    user_input = st.text_input("Zadej svou přezdívku:").lower().strip()
    if st.button("Vstoupit"):
        if user_input:
            st.session_state["username"] = user_input
            localS.setItem("gc_user", user_input)
            st.rerun()
        else:
            st.error("Jméno nesmí být prázdné!")
    st.stop()

# --- KONFIGURACE DATABÁZE ---
SUPABASE_URL = "https://ycwkedvzyhsofbuhludk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inljd2tlZHZ6eWhzb2ZidWhsdWRrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3NzUxNTMsImV4cCI6MjA5MDM1MTE1M30.ai6oiGESIWk4dxIG_tFb8FOuTMEhNeaymE7eWLpTsnk"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

CACHE_TYPES = ["💚Traditional💚","🧡Multi🧡","💙Mystery💙","🩵Virtual🩵","🌍Earthcache🌍","📬Letterbox📬","🧭Wherigo🧭","❤️Event❤️","🪾CITO🪾"]
SIZES = ["micro","small","regular","large","other"]
ATTRIBUTES = ["👶děti👶","🐶psi🐶","🛠️speciální nástroj🛠️","🚗drive-in🚗","🔭vyhlídka🔭","🌞24/7🌞"]

# --- FUNKCE ---
def load_data():
    try:
        res = supabase.table("treasures").select("*").eq("user_id", st.session_state["username"]).execute()
        data = res.data or []
        if not data:
            res_templates = supabase.table("treasures").select("*").is_("user_id", "null").execute()
            templates = res_templates.data or []
            if templates:
                for t in templates:
                    new_t = t.copy()
                    if "id" in new_t: del new_t["id"]
                    new_t["user_id"] = st.session_state["username"]
                    supabase.table("treasures").insert(new_t).execute()
                res = supabase.table("treasures").select("*").eq("user_id", st.session_state["username"]).execute()
                data = res.data or []
        
        clean = []
        for t in data:
            clean.append({
                "name": str(t.get("name", "")),
                "types": t.get("types") or [],
                "sizes": t.get("sizes") or [],
                "attrs": t.get("attrs") or [],
                "terrain_min": float(t.get("terrain_min") or 0.5),
                "terrain_max": float(t.get("terrain_max") or 5.0),
                "difficulty_min": float(t.get("difficulty_min") or 0.5),
                "difficulty_max": float(t.get("difficulty_max") or 5.0),
                "fav_min": int(t.get("fav_min") or 0),
                "remaining": max(0, int(t.get("remaining") or 0))
            })
        return clean
    except: return []

def save():
    try:
        supabase.table("treasures").delete().eq("user_id", st.session_state["username"]).execute()
        for t in st.session_state.treasures:
            t["user_id"] = st.session_state["username"]
            supabase.table("treasures").insert(t).execute()
        st.toast("Uloženo!", icon="💾")
    except Exception as e: st.error(f"Chyba: {e}")

# --- SESSION STATE ---
if "treasures" not in st.session_state:
    st.session_state.treasures = load_data()

# Pomocné stavy pro resetování formulářů
if "reset_cache_key" not in st.session_state: st.session_state.reset_cache_key = 0
if "reset_form_key" not in st.session_state: st.session_state.reset_form_key = 1000

for key, val in {"show_list": False, "open_detail": None, "open_detail_result": None, 
                 "edit_index": None, "results": [], "confirm_use": None, "confirm_delete": None}.items():
    if key not in st.session_state: st.session_state[key] = val

# --- SIDEBAR ---
with st.sidebar:
    st.write(f"Uživatel: **{st.session_state['username']}**")
    if st.button("Odhlásit se"):
        localS.removeItem("gc_user")
        st.session_state["username"] = None
        st.rerun()

# --- 1. ZADEJ KEŠ ---
st.title("Geocaching – výběr pokladů")
st.header("Zadej keš")

# Používáme suffix s reset_cache_key pro vynucení resetu prvků
rk = st.session_state.reset_cache_key
c_col1, c_col2 = st.columns(2)
cache_type = c_col1.selectbox("Typ keše", CACHE_TYPES, key=f"ct_{rk}")
cache_size = c_col2.selectbox("Velikost", SIZES, key=f"cs_{rk}")
cache_difficulty = st.slider("Obtížnost", 0.5, 5.0, 0.5, 0.5, key=f"cd_{rk}")
cache_terrain = st.slider("Terén", 0.5, 5.0, 0.5, 0.5, key=f"cterr_{rk}")
cache_fav = st.number_input("Srdíčka", 0, 10000, 0, key=f"cf_{rk}")
cache_attrs = st.multiselect("Atributy keše", ATTRIBUTES, key=f"ca_{rk}")

btn_col1, btn_col2 = st.columns(2)
if btn_col1.button("Vyhodnotit", use_container_width=True, type="primary"):
    results = []
    for i, t in enumerate(st.session_state.treasures):
        m = True
        if t["types"] and cache_type not in t["types"]: m = False
        if not (t["terrain_min"] <= cache_terrain <= t["terrain_max"]): m = False
        if not (t["difficulty_min"] <= cache_difficulty <= t["difficulty_max"]): m = False
        if t["sizes"] and cache_size not in t["sizes"]: m = False
        if cache_fav < t["fav_min"]: m = False
        if not set(t["attrs"]).issubset(set(cache_attrs)): m = False
        if m: results.append((i, t))
    st.session_state.results = sorted(results, key=lambda x: x[1]["remaining"])

if btn_col2.button("Reset", use_container_width=True):
    st.session_state.reset_cache_key += 1
    st.session_state.results = []
    st.rerun()

# Výsledky
if st.session_state.results:
    st.subheader("Vhodné poklady:")
    for i, t in st.session_state.results:
        r_col1, r_col2, r_col3, r_col4 = st.columns([4,2,1,1])
        r_col1.write(t["name"])
        r_col2.write(f"Zbývá: {t['remaining']}")
        if r_col3.button("ℹ️", key=f"res_i_{i}"):
            st.session_state.open_detail_result = i if st.session_state.open_detail_result != i else None
        if r_col4.button("✅", key=f"use_{i}"):
            st.session_state.confirm_use = i
        
        if st.session_state.open_detail_result == i:
            st.info(f"T {t['terrain_min']}-{t['terrain_max']} | D {t['difficulty_min']}-{t['difficulty_max']} | FP {t['fav_min']}+")
        
        if st.session_state.confirm_use == i:
            if st.button(f"Potvrdit použití {t['name']}", key=f"y_{i}"):
                if st.session_state.treasures[i]["remaining"] > 0:
                    st.session_state.treasures[i]["remaining"] -= 1
                    save()
                st.session_state.confirm_use = None
                st.rerun()

# --- 2. SEZNAM POKLADŮ ---
st.divider()
if "expanded_info" not in st.session_state:
    st.session_state.expanded_info = set()

if st.button("Zobrazit / skrýt seznam pokladů"):
    st.session_state.show_list = not st.session_state.show_list

if st.session_state.show_list:
    st.header("Seznam pokladů")
    
    # 1. Seskupíme poklady podle jména
    grouped = {}
    for i, t in enumerate(st.session_state.treasures):
        name = t["name"]
        if name not in grouped:
            grouped[name] = []
        grouped[name].append((i, t)) # ukládáme původní index a data

    # 2. Vytvoříme seznam skupin pro řazení (podle nejmenšího 'remaining' v dané skupině)
    group_list = []
    for name, variants in grouped.items():
        min_rem = min(v[1]["remaining"] for v in variants)
        group_list.append({"name": name, "variants": variants, "min_rem": min_rem})

    # 3. Seřadíme skupiny od nejméně zbývajících
    group_list = sorted(group_list, key=lambda x: x["min_rem"])

    if not group_list:
        st.write("Seznam je prázdný.")

    for group in group_list:
        name = group["name"]
        variants = group["variants"]
        is_expanded = name in st.session_state.expanded_info
        eye_icon = "🕶️" if is_expanded else "👁️"
        
        # Výpočet celkového počtu kusů pro hlavní řádek
        total_remaining = sum(v[1]["remaining"] for v in variants)

        # HLAVNÍ ŘÁDEK SKUPINY (Jeden řádek pro jeden název)
        col_name, col_eye, col_edit, col_del = st.columns([5, 1, 1, 1])
        
        col_name.write(f"**{name}** ({total_remaining})")
        
        # Oko přepíná zobrazení všech variant pod názvem
        if col_eye.button(eye_icon, key=f"eye_group_{name}"):
            if is_expanded:
                st.session_state.expanded_info.remove(name)
            else:
                st.session_state.expanded_info.add(name)
            st.rerun()

        # Editace první varianty (rychlá volba)
        if col_edit.button("🖌️", key=f"edit_group_{name}"):
            st.session_state.edit_index = variants[0][0]
            st.rerun()

        # Smazání CELÉ skupiny (všech duplikátů)
        if col_del.button("❌", key=f"del_group_{name}"):
            st.session_state.confirm_delete = name

        # POTVRZENÍ SMAZÁNÍ CELÉ SKUPINY
        if st.session_state.confirm_delete == name:
            st.error(f"Opravdu smazat VŠECHNY varianty pokladu '{name}'?")
            c1, c2 = st.columns(2)
            if c1.button("Ano, smazat vše", key=f"conf_yes_all_{name}"):
                st.session_state.treasures = [t for t in st.session_state.treasures if t["name"] != name]
                save()
                st.session_state.confirm_delete = None
                st.rerun()
            if c2.button("Zrušit", key=f"conf_no_all_{name}"):
                st.session_state.confirm_delete = None
                st.rerun()

        # ROZBALENÉ VARIANTY (DUPLIKÁTY)
        if is_expanded:
            for original_idx, t_var in variants:
                with st.container():
                    st.markdown(f"**Varianta (zbývá {t_var['remaining']}):**")
                    st.markdown(f"""
                    > 🌍 **Typy:** {", ".join(t_var['types']) if t_var['types'] else "Všechny"} | 📦 **Velikosti:** {", ".join(t_var['sizes']) if t_var['sizes'] else "Všechny"}  
                    > 📈 **T:** {t_var['terrain_min']}–{t_var['terrain_max']} | **D:** {t_var['difficulty_min']}–{t_var['difficulty_max']} | ❤️ **FP:** {t_var['fav_min']}+  
                    > 🏷️ **Atributy:** {", ".join(t_var['attrs']) if t_var['attrs'] else "Žádné"}
                    """)
                    
                    v_col1, v_col2, _ = st.columns([1, 1, 4])
                    # Editace konkrétní varianty
                    if v_col1.button("✏️", key=f"inner_edit_{original_idx}"):
                        st.session_state.edit_index = original_idx
                        st.rerun()
                    # Smazání konkrétní varianty
                    if v_col2.button("🗑️", key=f"inner_del_{original_idx}"):
                        st.session_state.treasures.pop(original_idx)
                        save()
                        st.rerun()
                st.divider()

# --- 3. FORMULÁŘ PŘIDAT / UPRAVIT ---
st.divider()
st.header("Přidat / upravit poklad")

# Výchozí hodnoty
d = {"name": "", "types": [], "terrain_min": 0.5, "terrain_max": 5.0, "difficulty_min": 0.5, "difficulty_max": 5.0, "sizes": [], "fav_min": 0, "attrs": [], "remaining": 0}
if st.session_state.edit_index is not None:
    d = st.session_state.treasures[st.session_state.edit_index]

fk = st.session_state.reset_form_key
f_name = st.text_input("Název", value=d["name"], key=f"fn_{fk}")
f_types = st.multiselect("Typy keší", CACHE_TYPES, default=d["types"], key=f"ft_{fk}")
f_sizes = st.multiselect("Velikosti", SIZES, default=d["sizes"], key=f"fs_{fk}")
f_diff = st.slider("Obtížnost (min-max)", 0.5, 5.0, (d["difficulty_min"], d["difficulty_max"]), 0.5, key=f"fd_{fk}")
f_terr = st.slider("Terén (min-max)", 0.5, 5.0, (d["terrain_min"], d["terrain_max"]), 0.5, key=f"fterr_{fk}")
f_fav = st.number_input("Min. srdíčka", 0, 1000, value=d["fav_min"], key=f"ff_{fk}")
f_attrs = st.multiselect("Atributy", ATTRIBUTES, default=d["attrs"], key=f"fa_{fk}")
f_rem = st.number_input("Zbývá kusů", 0, 100, value=d["remaining"], key=f"fr_{fk}")

b_col1, b_col2 = st.columns(2)
if b_col1.button("Uložit poklad", use_container_width=True, type="primary"):
    new_data = {
        "name": f_name, "types": f_types, "sizes": f_sizes,
        "difficulty_min": f_diff[0], "difficulty_max": f_diff[1],
        "terrain_min": f_terr[0], "terrain_max": f_terr[1],
        "fav_min": f_fav, "attrs": f_attrs, "remaining": f_rem
    }
    if st.session_state.edit_index is None:
        st.session_state.treasures.append(new_data)
    else:
        st.session_state.treasures[st.session_state.edit_index] = new_data
        st.session_state.edit_index = None
    save()
    st.rerun()

if b_col2.button("Reset formuláře", use_container_width=True):
    st.session_state.edit_index = None
    st.session_state.reset_form_key += 1 # Změna klíče "smaže" inputy
    st.rerun()
