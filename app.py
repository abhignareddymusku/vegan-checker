import re, json
import pandas as pd
import streamlit as st

lookup = json.load(open("lookup.json"))
df = pd.read_csv("products.csv.gz", dtype=str).fillna("")
df["search"] = (df["name"] + " " + df["brand"]).str.lower()

FLAG = re.compile(r"\b(collagen|keratin|elastin|tallow|lanolin|beeswax|cera alba|honey|"
    r"milk|lactose|casein|whey|silk|albumen|placenta|gelatin|carmine|cochineal|shellac|"
    r"guanine|chitosan|propolis|ambergris|musk|civet|snail|pearl)\b")

def check(text):
    items = re.split(r",(?!\d)|;|\n", text.lower())
    nv, am, fl, unk = [], [], [], []
    for item in items:
        item = re.sub(r"[\d.]+\s*%", "", item).strip().strip(" .*")
        if not item or item.isdigit():
            continue
        inner = re.findall(r"\((.*?)\)", item)
        base = re.sub(r"\(.*?\)", "", item).strip()
        cands = [base] + inner + [p.strip() for p in base.split("/")]
        hits = [lookup[c] for c in cands if c in lookup]
        if "Not vegan" in hits:   nv.append(item)
        elif "Ambiguous" in hits: am.append(item)
        elif "Vegan" in hits:     pass
        elif FLAG.search(item):   fl.append(item)
        else:                     unk.append(item)
    if nv:          r = "Not vegan"
    elif fl:        r = "Unclear"
    elif unk or am: r = "Likely vegan"
    else:           r = "Vegan"
    return r, nv, fl, am, unk

def show(text):
    r, nv, fl, am, unk = check(text)
    {"Vegan": st.success, "Likely vegan": st.info,
     "Unclear": st.warning, "Not vegan": st.error}[r](r)
    if nv:  st.write("**Animal-derived:**", ", ".join(nv))
    if fl:  st.write("**Needs checking:**", ", ".join(fl))
    if am:  st.write("**Source unverified (plant or animal):**", ", ".join(am))
    if unk: st.caption(f"{len(unk)} ingredients not in our list")

st.title("🌱 Vegan ingredient checker")
st.caption("Guidance only. Always check the product label. Product data from Open Beauty Facts (ODbL).")
tab1, tab2 = st.tabs(["Search product", "Paste ingredients"])

with tab1:
    q = st.text_input("Product name, brand, or barcode").strip().lower()
    if q:
        m = df[df["search"].str.contains(q, regex=False) | (df["barcode"] == q)].head(10)
        if m.empty:
            st.write("Not found. Try the Paste ingredients tab.")
        for _, row in m.iterrows():
            with st.expander(f'{row["name"]} - {row["brand"]}'):
                show(row["ingredients"])

with tab2:
    txt = st.text_area("Paste the ingredient list")
    if txt:
        show(txt)
