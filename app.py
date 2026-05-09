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

# --- 3. LOGIKA PŘIHLÁŠENÍ S PAMĚTÍ A HESLEM ---
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
                        st.error("Nesprávné heslo pro tohoto uživatele!")
                elif status == "new":
                    st.session_state.confirm_new_user = True
                    st.rerun()
                else:
                    st.error(f"Chyba databáze: {db_password}")
            else:
                st.error("Vyplň jméno i heslo!")
    else:
        st.warning(f"Uživatel **{u_input}** neexistuje. Chceš vytvořit nový účet?")
        c1, c2 = st.columns(2)
        if c1.button("Ano, vytvořit", type="primary", use_container_width=True):
            try:
                supabase.table("treasures").insert({
                    "user_id": u_input, 
                    "password": p_input,
                    "name": "_INITIAL_STATE_", 
                    "remaining": 0
                }).execute()
                st.session_state["username"] = u_input
                st.session_state["logged_in"] = True
                st.session_state["current_password"] = p_input 
                st.session_state.confirm_new_user = False
                localS.setItem("gc_user", u_input)
                st.query_params["user"] = u_input
                st.rerun()
            except Exception as e:
                st.error(f"Nepodařilo se založit účet: {e}")
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

def import_templates():
    try:
        # Načteme šablony (řádky, kde user_id je null)
        res_templates = supabase.table("treasures").select("*").is_("user_id", "null").execute()
        templates = res_templates.data or []
        if templates:
            for t in templates:
                new_t = t.copy()
                if "id" in new_t: del new_t["id"]
                new_t["user_id"] = st.session_state["username"]
                if "current_password" in st.session_state:
                    new_t["password"] = st.session_state["current_password"]
                supabase.table("treasures").insert(new_t).execute()
            st.session_state.treasures = load_data()
            st.toast("Balíček šablon stažen!", icon="📥")
            st.rerun()
        else:
            st.error("V databázi nebyly nalezeny žádné šablony.")
    except Exception as e:
        st.error(f"Chyba při importu: {e}")

def save():
    try:
        supabase.table("treasures").delete().eq("user_id", st.session_state["username"]).execute()
        # Zpětně vložíme inicializační řádek, aby v DB zůstalo heslo i při prázdném seznamu
        supabase.table("treasures").insert({
            "user_id": st.session_state["username"], 
            "password": st.session_state.get("current_password"),
            "name": "_INITIAL_STATE_", "remaining": 0
        }).execute()
        for t in st.session_state.treasures:
            t_to_save = t.copy()
            t_to_save["user_id"] = st.session_state["username"]
            if "current_password" in st.session_state:
                t_to_save["password"] = st.session_state["current_password"]
            supabase.table("treasures").insert(t_to_save).execute()
        st.toast("Uloženo!", icon="💾")
    except Exception as e: 
        st.error(f"Chyba při ukládání: {e}")

def delete_account():
    try:
        supabase.table("treasures").delete().eq("user_id", st.session_state["username"]).execute()
        localS.deleteItem("gc_user")
        st.session_state["username"] = None
        st.session_state["logged_in"] = False
        if "treasures" in st.session_state: del st.session_state["treasures"]
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Chyba při mazání účtu: {e}")

# --- 6. SESSION STATE ---
if "treasures" not in st.session_state:
    st.session_state.treasures = load_data()

if "reset_cache_key" not in st.session_state: st.session_state.reset_cache_key = 0
if "reset_form_key" not in st.session_state: st.session_state.reset_form_key = 1000

for key, val in {"show_list": False, "open_detail": None, "open_detail_result": None, 
                 "edit_index": None, "results": [], "confirm_use": None, "confirm_delete": None}.items():
    if key not in st.session_state: st.session_state[key] = val

# --- 7. SIDEBAR ---
with st.sidebar:
    st.write(f"Uživatel: **{st.session_state['username']}**")
    
    if st.button("Odhlásit se", use_container_width=True):
        localS.deleteItem("gc_user")
        st.session_state["username"] = None
        st.session_state["logged_in"] = False
        if "treasures" in st.session_state: del st.session_state["treasures"]
        st.query_params.clear()
        st.rerun()
    
    st.divider()
    
    # NOVÉ: Tlačítko pro stažení šablon v sidebaru
    if st.button("📥 Stáhnout balíček šablon", use_container_width=True):
        import_templates()

    st.divider()
    
    if "confirm_delete_account" not in st.session_state:
        st.session_state.confirm_delete_account = False
        
    if not st.session_state.confirm_delete_account:
        if st.button("Smazat účet 🗑️", use_container_width=True, type="secondary"):
            st.session_state.confirm_delete_account = True
            st.rerun()
    else:
        st.warning("Opravdu smazat účet?")
        col_del1, col_del2 = st.columns(2)
        if col_del1.button("ANO, SMAZAT", type="primary", use_container_width=True):
            delete_account()
        if col_del2.button("Zrušit", use_container_width=True):
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
            st.session_state.open_detail_result = i if st.session_state.open_detail_result != i else None
            st.rerun()
        if r_col4.button("✅", key=f"use_{i}"):
            st.session_state.confirm_use = i
        
        # --- SJEDNOCENÝ STYL INFORMAČNÍHO BLOKU ---
        if st.session_state.open_detail_result == i:
            with st.container():
                info_lines = []
                # Filtrujeme jen to, co není "univerzální"
                if t['types'] and len(t['types']) < len(CACHE_TYPES):
    # Tohle zajistí, že se emoji neodtrhne od textu
                    safe_types = [txt.replace(" ", "\u00A0") for txt in t['types']]
                    info_lines.append(f"➖ {', '.join(safe_types)}")
                if t['sizes'] and len(t['sizes']) < len(SIZES):
                    info_lines.append(f"➖ {', '.join(t['sizes'])}")
                if t['terrain_min'] > 0.5 or t['terrain_max'] < 5.0:
                    info_lines.append(f"➖ **T:** {t['terrain_min']}–{t['terrain_max']}")
                if t['difficulty_min'] > 0.5 or t['difficulty_max'] < 5.0:
                    info_lines.append(f"➖ **D:** {t['difficulty_min']}–{t['difficulty_max']}")
                if t['fav_min'] > 0:
                    info_lines.append(f"➖ **FP:** {t['fav_min']}+")
                if t['attrs']:
                    info_lines.append(f"➖ **Atributy:** {', '.join(t['attrs'])}")
                
                if not info_lines:
                    st.info("Bez omezení.")
                else:
                    # Použití markdownu se odsazením (stejně jako u očička)
                    st.markdown("> " + "  \n> ".join(info_lines))
        
        if st.session_state.confirm_use == i:
            st.warning(f"Opravdu použít {t['name']}?")
            conf_col1, conf_col2 = st.columns(2)
            if conf_col1.button("Potvrdit ✅", key=f"y_{i}", use_container_width=True):
                target_name = t['name']
                for idx, item in enumerate(st.session_state.treasures):
                    if item["name"] == target_name:
                        st.session_state.treasures[idx]["remaining"] = max(0, item["remaining"] - 1)
                save()
                st.session_state.confirm_use = None
                st.session_state.results = []
                st.rerun()
            if conf_col2.button("Zrušit ❌", key=f"n_{i}", use_container_width=True):
                st.session_state.confirm_use = None
                st.rerun()
        if st.session_state.confirm_use == i:
            st.warning(f"Opravdu použít {t['name']}?")
            conf_col1, conf_col2 = st.columns(2)
            if conf_col1.button("Potvrdit ✅", key=f"y_{i}", use_container_width=True):
                target_name = t['name']
                for idx, item in enumerate(st.session_state.treasures):
                    if item["name"] == target_name:
                        st.session_state.treasures[idx]["remaining"] = max(0, item["remaining"] - 1)
                save()
                st.session_state.confirm_use = None
                st.session_state.results = []
                st.rerun()
            if conf_col2.button("Zrušit ❌", key=f"n_{i}", use_container_width=True):
                st.session_state.confirm_use = None
                st.rerun()

# --- 9. SEZNAM POKLADŮ ---
st.divider()
if "expanded_info" not in st.session_state:
    st.session_state.expanded_info = set()
# Přidaná inicializace pro výběr varianty
if "ask_which_variant" not in st.session_state:
    st.session_state.ask_which_variant = None

if st.button("Zobrazit / skrýt seznam pokladů"):
    st.session_state.show_list = not st.session_state.show_list

if st.session_state.show_list:
    st.header("Seznam pokladů")
    
    if not st.session_state.treasures:
        st.info("Tvůj seznam pokladů je prázdný.")
        st.write("Chceš stáhnout základní balíček šablon?")
        if st.button("Ano, stáhnout balíček ✅", type="primary"):
            import_templates()
    else:
        grouped = {}
        for i, t in enumerate(st.session_state.treasures):
            name = t["name"]
            if name not in grouped: grouped[name] = []
            grouped[name].append((i, t))

        group_list = []
        for name, variants in grouped.items():
            min_rem = min(v[1]["remaining"] for v in variants)
            group_list.append({"name": name, "variants": variants, "min_rem": min_rem})
        
        group_list = sorted(group_list, key=lambda x: x["min_rem"])

        for group in group_list:
            name = group["name"]
            variants = group["variants"]
            is_expanded = name in st.session_state.expanded_info
            eye_icon = "🕶️" if is_expanded else "👁️"
            current_stock = max(v[1]["remaining"] for v in variants)

            col_name, col_eye, col_edit, col_del = st.columns([5, 1, 1, 1])
            col_name.write(f"{name} ({current_stock})")
            
            if col_eye.button(eye_icon, key=f"eye_group_{name}"):
                if is_expanded: st.session_state.expanded_info.remove(name)
                else: st.session_state.expanded_info.add(name)
                st.rerun()

            # UPRAVENÁ LOGIKA EDITACE:
            if col_edit.button("🖌️", key=f"edit_group_{name}"):
                if len(variants) == 1:
                    st.session_state.edit_index = variants[0][0]
                    st.session_state.reset_form_key += 1
                    st.rerun()
                else:
                    # Pokud je jich víc, aktivujeme dotaz
                    st.session_state.ask_which_variant = name
                    st.rerun()

# --- OPRAVENÁ LOGIKA MAZÁNÍ A EDITACE ---
            
            # 1. Tlačítko pro smazání (X)
            if col_del.button("❌", key=f"del_group_{name}"):
                if len(variants) == 1:
                    st.session_state.confirm_delete = name
                else:
                    st.session_state.ask_which_delete = name
                st.rerun()

            # 2. SCÉNÁŘ: Mazání u duplikátů (výběr varianty)
            if st.session_state.get("ask_which_delete") == name:
                st.warning(f"Kterou variantu '{name}' chceš smazat?")
                for v_idx, v_data in variants:
                    v_label = f"Smazat: {', '.join(v_data['types']) if v_data['types'] else 'Všechny typy'}"
                    if st.button(v_label, key=f"select_del_btn_{v_idx}", use_container_width=True):
                        st.session_state.treasures.pop(v_idx)
                        save()
                        st.session_state.ask_which_delete = None
                        st.rerun()
                
                st.divider()
                if st.button(f"🗑️ SMAZAT ÚPLNĚ VŠE ({name})", key=f"del_complete_all_{name}", type="primary", use_container_width=True):
                    st.session_state.treasures = [t for t in st.session_state.treasures if t["name"] != name]
                    save()
                    st.session_state.ask_which_delete = None
                    st.rerun()
                
                if st.button("Zpět", key=f"cancel_del_sel_{name}", use_container_width=True):
                    st.session_state.ask_which_delete = None
                    st.rerun()

            # 3. SCÉNÁŘ: Mazání u jedné položky (potvrzení Ano/Ne)
            if st.session_state.confirm_delete == name:
                st.error(f"Opravdu smazat '{name}'?")
                c1, c2 = st.columns(2)
                if c1.button("Ano", key=f"single_conf_yes_{name}", use_container_width=True):
                    st.session_state.treasures = [t for t in st.session_state.treasures if t["name"] != name]
                    save()
                    st.session_state.confirm_delete = None
                    st.rerun()
                if c2.button("Ne", key=f"single_conf_no_{name}", use_container_width=True):
                    st.session_state.confirm_delete = None
                    st.rerun()

            # 4. SCÉNÁŘ: Výběr varianty pro EDITACI
            if st.session_state.ask_which_variant == name:
                st.info(f"Kterou variantu '{name}' chceš upravit?")
                for v_idx, v_data in variants:
                    v_label = f"Typy: {', '.join(v_data['types'])}" if v_data['types'] else "Všechny typy (univerzální)"
                    if st.button(v_label, key=f"select_edit_{v_idx}", use_container_width=True):
                        st.session_state.edit_index = v_idx
                        st.session_state.ask_which_variant = None
                        st.session_state.reset_form_key += 1
                        st.rerun()
                
                if st.button("Zrušit výběr", key=f"cancel_select_{name}", use_container_width=True):
                    st.session_state.ask_which_variant = None
                    st.rerun()

            if is_expanded:
                for original_idx, t_var in variants:
                    with st.container():
                        info_lines = []
                        if t_var['types'] and len(t_var['types']) < len(CACHE_TYPES):
    # Stejný trik pro seznam pokladů
                           safe_types_var = [txt.replace(" ", "\u00A0") for txt in t_var['types']]
                           info_lines.append(f"➖ {', '.join(safe_types_var)}")
                        if t_var['sizes'] and len(t_var['sizes']) < len(SIZES):
                            info_lines.append(f"➖ {', '.join(t_var['sizes'])}")
                        if t_var['terrain_min'] > 0.5 or t_var['terrain_max'] < 5.0:
                            info_lines.append(f"➖ **T:** {t_var['terrain_min']}–{t_var['terrain_max']}")
                        if t_var['difficulty_min'] > 0.5 or t_var['difficulty_max'] < 5.0:
                            info_lines.append(f"➖ **D:** {t_var['difficulty_min']}–{t_var['difficulty_max']}")
                        if t_var['fav_min'] > 0:
                            info_lines.append(f"➖ **FP:** {t_var['fav_min']}+")
                        if t_var['attrs']:
                            info_lines.append(f"➖ **Atributy:** {', '.join(t_var['attrs'])}")
                        if not info_lines: st.info("Bez omezení.")
                        else: st.markdown("> " + "  \n> ".join(info_lines))
# --- 10. FORMULÁŘ PŘIDAT / UPRAVIT ---
st.divider()

if st.session_state.edit_index is not None:
    # Kontrola pro jistotu, aby index nebyl mimo rozsah
    if st.session_state.edit_index < len(st.session_state.treasures):
        st.header(f"Upravit: {st.session_state.treasures[st.session_state.edit_index]['name']}")
        d = st.session_state.treasures[st.session_state.edit_index]
    else:
        st.session_state.edit_index = None
        st.rerun()
else:
    st.header("Přidat nový poklad")
    d = {"name": "", "types": [], "terrain_min": 0.5, "terrain_max": 5.0, "difficulty_min": 0.5, "difficulty_max": 5.0, "sizes": [], "fav_min": 0, "attrs": [], "remaining": 0}

fk = st.session_state.reset_form_key
f_name = st.text_input("Název", value=str(d["name"]), key=f"fn_{fk}")
f_types = st.multiselect("Typy", CACHE_TYPES, default=d["types"], key=f"ft_{fk}")
f_sizes = st.multiselect("Velikosti", SIZES, default=d["sizes"], key=f"fs_{fk}")

# Explicitní přetypování na float pro slider, aby nedocházelo k chybám typu
f_diff = st.slider("Obtížnost", 0.5, 5.0, (float(d["difficulty_min"]), float(d["difficulty_max"])), 0.5, key=f"fd_{fk}")
f_terr = st.slider("Terén", 0.5, 5.0, (float(d["terrain_min"]), float(d["terrain_max"])), 0.5, key=f"fterr_{fk}")
f_fav = st.number_input("Min. srdíčka", 0, 10000, value=int(d["fav_min"]), key=f"ff_{fk}")
f_attrs = st.multiselect("Atributy", ATTRIBUTES, default=d["attrs"], key=f"fa_{fk}")
f_rem = st.number_input("Zbývá kusů", 0, 1000, value=int(d["remaining"]), key=f"fr_{fk}")

b_col1, b_col2 = st.columns(2)

# Logika pro uložení
if b_col1.button("Uložit poklad", use_container_width=True, type="primary"):
    if f_name:
        new_entry = {
            "name": f_name, 
            "types": f_types, 
            "sizes": f_sizes, 
            "difficulty_min": float(f_diff[0]), "difficulty_max": float(f_diff[1]), 
            "terrain_min": float(f_terr[0]), "terrain_max": float(f_terr[1]), 
            "fav_min": int(f_fav), 
            "attrs": f_attrs, 
            "remaining": int(f_rem)
        }

        # SCÉNÁŘ A: Klasická úprava (Edit mode) - Teď upravujeme přesně ten jeden vybraný index
        if st.session_state.edit_index is not None:
            st.session_state.treasures[st.session_state.edit_index] = new_entry
            save()
            st.session_state.edit_index = None
            st.rerun()
        
        # SCÉNÁŘ B: Kontrola duplikátu POUZE při přidávání nového
        else:
            dup_idx = None
            for idx, item in enumerate(st.session_state.treasures):
                if item["name"].lower() == f_name.lower():
                    dup_idx = idx
                    break
            
            if dup_idx is not None:
                # Našli jsme shodu, vyvoláme dialog (to se stane jen při tvorbě nového)
                st.session_state.duplicate_pending = new_entry
                st.rerun()
            else:
                # Žádná shoda, rovnou přidáme jako nový záznam
                st.session_state.treasures.append(new_entry)
                save()
                st.rerun()

if b_col2.button("Zrušit", use_container_width=True):
    st.session_state.edit_index = None
    st.session_state.reset_form_key += 1
    if "duplicate_pending" in st.session_state: 
        del st.session_state.duplicate_pending
    st.rerun()

# --- ŘEŠENÍ DUPLIKÁTŮ (Dialog pod formulářem - aktivuje se jen u nového záznamu) ---
if "duplicate_pending" in st.session_state:
    pending = st.session_state.duplicate_pending
    st.warning(f"Poklad se jménem **{pending['name']}** už v seznamu existuje. Co chceš udělat?")
    d_col1, d_col2, d_col3 = st.columns(3)
    
    if d_col1.button("Upravit stávající", key="dup_update", use_container_width=True):
        # Najdeme první výskyt a ten přepíšeme
        for idx, item in enumerate(st.session_state.treasures):
            if item["name"].lower() == pending["name"].lower():
                st.session_state.treasures[idx] = pending
                break
        save()
        del st.session_state.duplicate_pending
        st.rerun()
        
    if d_col2.button("Přidat jako další duplikát", key="dup_add", use_container_width=True):
        st.session_state.treasures.append(pending)
        save()
        del st.session_state.duplicate_pending
        st.rerun()
        
    if d_col3.button("Zrušit", key="dup_cancel", use_container_width=True):
        del st.session_state.duplicate_pending
        st.rerun()
