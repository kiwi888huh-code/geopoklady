import streamlit as st
from supabase import create_client
from streamlit_local_storage import LocalStorage

# --- 1. KONFIGURACE DATABÁZE ---
SUPABASE_URL = "https://ycwkedvzyhsofbuhludk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inljd2tlZHZ6eWhzb2ZidWhsdWRrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ3NzUxNTMsImV4cCI6MjA5MDM1MTE1M30.ai6oiGESIWk4dxIG_tFb8FOuTMEhNeaymE7eWLpTsnk"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 2. INICIALIZACE ---
localS = LocalStorage()

if "username" not in st.session_state:
    st.session_state["username"] = None

# --- 3. LOGIKA PŘIHLÁŠENÍ ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "confirm_new_user" not in st.session_state:
    st.session_state["confirm_new_user"] = False

def check_user_status(username):
    try:
        res = supabase.table("treasures").select("password").eq("user_id", username).execute()
        if res.data and any(row.get("password") for row in res.data):
            pwd = next(row["password"] for row in res.data if row.get("password"))
            return "exists", pwd
        else:
            return "new", None
    except Exception as e:
        return "error", str(e)

if not st.session_state["logged_in"]:
    stored_user = localS.getItem("gc_user")
    url_user = st.query_params.get("user")
    if url_user or stored_user:
        st.session_state["username"] = (url_user or stored_user).lower().strip()
        st.session_state["logged_in"] = True

if not st.session_state["logged_in"]:
    st.title("Geocaching filtr – Přihlášení")
    u_input = st.text_input("Uživatelské jméno:", disabled=st.session_state.confirm_new_user).lower().strip()
    p_input = st.text_input("Heslo:", type="password", disabled=st.session_state.confirm_new_user)
    
    if not st.session_state.confirm_new_user:
        if st.button("Vstoupit"):
            if u_input and p_input:
                status, db_password = check_user_status(u_input)
                if status == "exists":
                    if db_password == p_input:
                        st.session_state["username"] = u_input
                        st.session_state["logged_in"] = True
                        st.session_state["current_password"] = p_input 
                        localS.setItem("gc_user", u_input)
                        st.query_params["user"] = u_input
                        st.rerun()
                    else:
                        st.error("Nesprávné heslo!")
                elif status == "new":
                    st.session_state.confirm_new_user = True
                    st.rerun()
                else:
                    st.error(f"Chyba: {db_password}")
            else:
                st.error("Vyplň jméno i heslo!")
    else:
        st.warning(f"Uživatel **{u_input}** neexistuje. Chceš vytvořit nový účet?")
        c1, c2 = st.columns(2)
        if c1.button("Ano, vytvořit", type="primary", use_container_width=True):
            try:
                supabase.table("treasures").insert({
                    "user_id": u_input, "password": p_input,
                    "name": "_INITIAL_STATE_", "remaining": 0
                }).execute()
                st.session_state["username"] = u_input
                st.session_state["logged_in"] = True
                st.session_state["current_password"] = p_input 
                st.session_state.confirm_new_user = False
                localS.setItem("gc_user", u_input)
                st.query_params["user"] = u_input
                st.rerun()
            except Exception as e:
                st.error(f"Chyba při založení: {e}")
        if c2.button("Ne, opravit údaje", use_container_width=True):
            st.session_state.confirm_new_user = False
            st.rerun()
    st.stop()

# --- 4. KONSTANTY ---
CACHE_TYPES = ["💚Traditional💚","🧡Multi🧡","💙Mystery💙","🩵Virtual🩵","🌍Earthcache🌍","📬Letterbox📬","🧭Wherigo🧭","❤️Event❤️","🪾CITO🪾"]
SIZES = ["micro","small","regular","large","other"]
ATTRIBUTES = ["👶děti👶","🐶psi🐶","🛠️speciální nástroj🛠️","🚗drive-in🚗","🔭vyhlídka🔭","🌞24/7🌞"]

# --- 5. FUNKCE ---
def load_data():
    try:
        res = supabase.table("treasures").select("*").eq("user_id", st.session_state["username"]).execute()
        data = res.data or []
        clean = []
        for t in data:
            if t.get("name") == "_INITIAL_STATE_": continue
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
        # Znovu vložíme startovací bod, aby uživatel nezmizel z DB při smazání všech pokladů
        supabase.table("treasures").insert({
            "user_id": st.session_state["username"], 
            "password": st.session_state.get("current_password"),
            "name": "_INITIAL_STATE_", "remaining": 0
        }).execute()
        for t in st.session_state.treasures:
            t_save = t.copy()
            t_save["user_id"] = st.session_state["username"]
            if "current_password" in st.session_state: t_save["password"] = st.session_state["current_password"]
            supabase.table("treasures").insert(t_save).execute()
        st.toast("Uloženo!", icon="💾")
    except Exception as e: st.error(f"Chyba: {e}")

def delete_account():
    try:
        supabase.table("treasures").delete().eq("user_id", st.session_state["username"]).execute()
        localS.deleteItem("gc_user")
        st.session_state["username"] = None
        st.session_state["logged_in"] = False
        if "treasures" in st.session_state: del st.session_state["treasures"]
        st.query_params.clear()
        st.rerun()
    except Exception as e: st.error(f"Chyba: {e}")

def import_templates():
    try:
        res = supabase.table("treasures").select("*").is_("user_id", "null").execute()
        templates = res.data or []
        if templates:
            for t in templates:
                nt = t.copy()
                if "id" in nt: del nt["id"]
                nt["user_id"] = st.session_state["username"]
                if "current_password" in st.session_state: nt["password"] = st.session_state["current_password"]
                supabase.table("treasures").insert(nt).execute()
            st.session_state.treasures = load_data()
            st.success("Balíček stažen!")
            st.rerun()
    except Exception as e: st.error(f"Chyba importu: {e}")

# --- 6. SESSION STATE ---
if "treasures" not in st.session_state:
    st.session_state.treasures = load_data()

for key, val in {"show_list": False, "edit_index": None, "results": [], "confirm_use": None, 
                 "confirm_delete": None, "reset_cache_key": 0, "reset_form_key": 1000}.items():
    if key not in st.session_state: st.session_state[key] = val

# --- 7. SIDEBAR ---
with st.sidebar:
    st.write(f"Uživatel: **{st.session_state['username']}**")
    if st.button("Odhlásit se", use_container_width=True):
        localS.deleteItem("gc_user")
        st.session_state["logged_in"] = False
        st.rerun()
    
    st.divider()
    if st.button("📥 Stáhnout balíček pokladů", use_container_width=True):
        import_templates()

    st.divider()
    if "confirm_delete_account" not in st.session_state: st.session_state.confirm_delete_account = False
    if not st.session_state.confirm_delete_account:
        if st.button("Smazat účet 🗑️", use_container_width=True, type="secondary"):
            st.session_state.confirm_delete_account = True
            st.rerun()
    else:
        st.warning("Smazat vše?")
        c1, c2 = st.columns(2)
        if c1.button("ANO", type="primary", use_container_width=True): delete_account()
        if c2.button("NE", use_container_width=True):
            st.session_state.confirm_delete_account = False
            st.rerun()

# --- 8. HLAVNÍ OBSAH (ZADEJ KEŠ) ---
st.title("Geocaching – výběr pokladů")
st.header("Zadej keš")

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

if st.session_state.results:
    st.subheader("Vhodné poklady:")
    for i, t in st.session_state.results:
        r_col1, r_col2, r_col3, r_col4 = st.columns([4, 2, 1, 1])
        r_col1.write(t["name"])
        r_col2.write(f"Zbývá: {t['remaining']}")
        if r_col3.button("ℹ️", key=f"res_i_{i}"):
            st.info(f"T {t['terrain_min']}-{t['terrain_max']} | D {t['difficulty_min']}-{t['difficulty_max']} | FP {t['fav_min']}+")
        if r_col4.button("✅", key=f"use_{i}"):
            st.session_state.confirm_use = i
        
        if st.session_state.confirm_use == i:
            st.warning(f"Použít {t['name']}?")
            conf_col1, conf_col2 = st.columns(2)
            if conf_col1.button("ANO ✅", key=f"y_{i}"):
                for idx, item in enumerate(st.session_state.treasures):
                    if item["name"] == t["name"]: st.session_state.treasures[idx]["remaining"] = max(0, item["remaining"] - 1)
                save()
                st.session_state.confirm_use = None
                st.session_state.results = []
                st.rerun()
            if conf_col2.button("NE ❌", key=f"n_{i}"):
                st.session_state.confirm_use = None
                st.rerun()

# --- 9. SEZNAM POKLADŮ ---
st.divider()
if st.button("Zobrazit / skrýt seznam pokladů", use_container_width=True):
    st.session_state.show_list = not st.session_state.show_list

if st.session_state.show_list:
    st.header("Seznam pokladů")
    if not st.session_state.treasures:
        st.info("Tvůj seznam je prázdný.")
        if st.button("📥 Stáhnout základní balíček?", type="primary"): import_templates()
    else:
        grouped = {}
        for i, t in enumerate(st.session_state.treasures):
            if t["name"] not in grouped: grouped[t["name"]] = []
            grouped[t["name"]].append((i, t))
        
        for name, variants in sorted(grouped.items()):
            col_n, col_ed, col_de = st.columns([6, 1, 1])
            stock = max(v[1]["remaining"] for v in variants)
            col_n.write(f"**{name}** ({stock} ks)")
            if col_ed.button("🖌️", key=f"ed_{name}"):
                st.session_state.edit_index = variants[0][0]
                st.rerun()
            if col_de.button("❌", key=f"de_{name}"):
                st.session_state.confirm_delete = name
            
            if st.session_state.confirm_delete == name:
                c1, c2 = st.columns(2)
                if c1.button("Smazat", key=f"cy_{name}"):
                    st.session_state.treasures = [t for t in st.session_state.treasures if t["name"] != name]
                    save()
                    st.session_state.confirm_delete = None
                    st.rerun()
                if c2.button("Zrušit", key=f"cn_{name}"):
                    st.session_state.confirm_delete = None
                    st.rerun()

# --- 10. FORMULÁŘ ---
st.divider()
if st.session_state.edit_index is not None:
    st.header(f"Upravit: {st.session_state.treasures[st.session_state.edit_index]['name']}")
    d = st.session_state.treasures[st.session_state.edit_index]
else:
    st.header("Přidat nový poklad")
    d = {"name":"", "types":[], "terrain_min":0.5, "terrain_max":5.0, "difficulty_min":0.5, "difficulty_max":5.0, "sizes":[], "fav_min":0, "attrs":[], "remaining":0}

fk = st.session_state.reset_form_key
f_name = st.text_input("Název", value=str(d["name"]), key=f"fn_{fk}")
f_types = st.multiselect("Typy", CACHE_TYPES, default=d["types"], key=f"ft_{fk}")
f_sizes = st.multiselect("Velikosti", SIZES, default=d["sizes"], key=f"fs_{fk}")
f_diff = st.slider("Obtížnost", 0.5, 5.0, (float(d["difficulty_min"]), float(d["difficulty_max"])), 0.5, key=f"fd_{fk}")
f_terr = st.slider("Terén", 0.5, 5.0, (float(d["terrain_min"]), float(d["terrain_max"])), 0.5, key=f"fterr_{fk}")
f_rem = st.number_input("Zbývá kusů", 0, 1000, value=int(d["remaining"]), key=f"fr_{fk}")

b1, b2 = st.columns(2)
if b1.button("Uložit", use_container_width=True, type="primary"):
    if f_name:
        new_data = {"name": f_name, "types": f_types, "sizes": f_sizes, "difficulty_min": f_diff[0], "difficulty_max": f_diff[1], "terrain_min": f_terr[0], "terrain_max": f_terr[1], "fav_min": d["fav_min"], "attrs": d["attrs"], "remaining": f_rem}
        if st.session_state.edit_index is None: st.session_state.treasures.append(new_data)
        else: st.session_state.treasures[st.session_state.edit_index] = new_data
        save()
        st.session_state.edit_index = None
        st.rerun()
if b2.button("Zrušit editaci", use_container_width=True):
    st.session_state.edit_index = None
    st.rerun()
