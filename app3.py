import streamlit as st
from search_engine import search_image
from PIL import Image
import random

# -----------------------------
# SESSION STATE INIT
# -----------------------------
if "page" not in st.session_state:
    st.session_state["page"] = "home"

if "selected_product" not in st.session_state:
    st.session_state["selected_product"] = None

if "results_cache" not in st.session_state:
    st.session_state["results_cache"] = None

if "query_image" not in st.session_state:
    st.session_state["query_image"] = None

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="PPC Sight Match", layout="wide")

# -----------------------------
# STYLES
# -----------------------------
st.markdown("""
<style>
.amazon-bar {
    background-color: #0f172a;
    padding: 18px;
    border-radius: 18px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.search-box {
    background: rgba(255,255,255,0.08);
    padding: 14px 20px;
    border-radius: 30px;
    width: 420px;
    color: gray;
}

.product-card {
    background: white;
    padding: 12px;
    border-radius: 12px;
    box-shadow: 0px 2px 10px rgba(0,0,0,0.25);
    text-align: center;
}

.price {
    font-size: 28px;
    font-weight: bold;
    color: #B12704;
}

.old-price {
    text-decoration: line-through;
    color: gray;
    margin-left: 10px;
}

.discount {
    color: green;
    font-weight: bold;
    margin-bottom: 12px;
}

.pdp-box {
    background: white;
    padding: 30px;
    border-radius: 16px;
    box-shadow: 0px 4px 20px rgba(0,0,0,0.25);
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# ✅ SIDEBAR: UPLOAD + PREVIEW BELOW UPLOAD (FIXED)
# =========================================================
with st.sidebar:
    st.markdown("## 📤 Upload Product Image")

    upload = st.file_uploader("Upload image", type=["jpg", "png", "jpeg"])
    camera = st.camera_input("Use camera")

    file_obj = None

    if upload:
        file_obj = upload
        st.session_state["query_image"] = Image.open(upload).convert("RGB")
        st.session_state["results_cache"] = None

    elif camera:
        file_obj = camera
        st.session_state["query_image"] = Image.open(camera).convert("RGB")
        st.session_state["results_cache"] = None

    st.markdown("---")
    st.markdown("### 🔎 Your Search Image")

    if st.session_state["query_image"] is not None:
        st.image(st.session_state["query_image"], use_container_width=True)
    else:
        st.info("No image uploaded yet")

# =============================
# ✅ HOME PAGE (SEARCH)
# =============================
if st.session_state["page"] == "home":

    st.markdown("""
        <div class="amazon-bar">
            <h1 style="color:white;">Sight <span style="color:#38bdf8">Match</span></h1>
            <div class="search-box">Search by image, product, or brand...</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Results")

    # ✅ Run search only once & cache it
    if st.session_state["query_image"] and st.session_state["results_cache"] is None:
        with st.spinner("Searching similar products..."):
            st.session_state["results_cache"] = search_image(file_obj, top_k=9)

    results = st.session_state["results_cache"]

    if results:
        cols = st.columns(3)
        for i, r in enumerate(results):
            with cols[i % 3]:
                with st.container(border=True):

                    img = Image.open(r["path"]).convert("RGB")
                    img = img.resize((240, 240))
                    st.image(img)

                    st.markdown(f"**{r.get('description','No description')}**")
                    st.markdown(f"Similarity: `{r['score']:.2f}`")

                    if st.button("🔍 View Product", key=f"p{i}"):
                        st.session_state["selected_product"] = r
                        st.session_state["page"] = "product"
                        st.rerun()

    else:
        st.info("Upload an image to start visual search.")

# =============================
# ✅ PRODUCT DETAILS PAGE (PDP)
# =============================
if st.session_state["page"] == "product":

    product = st.session_state["selected_product"]

    st.markdown("## 🛍 Product Details")

    col1, col2 = st.columns([1, 1])

    with col1:
        img = Image.open(product["path"]).convert("RGB")
        st.image(img, width=380)

    with col2:
        with st.container(border=True):
            st.markdown(f"## {product.get('description','Product')}")

            price = random.randint(999, 4999)
            discount = random.randint(15, 45)
            old_price = round(price * (1 + discount / 100))

            st.markdown(f"""
            <div class="price">₹{price} 
            <span class="old-price">₹{old_price}</span></div>
            <div class="discount">{discount}% OFF</div>
            """, unsafe_allow_html=True)

            st.markdown("### ✅ Features")
            st.write("""
            • Premium quality material  
            • Lightweight & breathable  
            • Durable stitching  
            • Trendy modern fit  
            • PPC certified quality  
            """)

            if st.button("🛒 Add To Cart"):
                st.success("Item added to cart successfully!")

    st.markdown("---")

    if st.button("⬅ Back to Search"):
        st.session_state["page"] = "home"
        st.rerun()
