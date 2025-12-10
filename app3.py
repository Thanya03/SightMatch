import streamlit as st
from search_engine import search_image
from PIL import Image

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(page_title="PPC Sight Match", layout="wide")

# -----------------------------
# Custom Amazon-like CSS
# -----------------------------
st.markdown("""
<style>
body {
    background-color: #f3f3f3;
}

.amazon-bar {
    background-color: #131921;
    padding: 12px;
    display: flex;
    justify-content: center;
}

.search-box {
    display: flex;
    background: white;
    border-radius: 6px;
    width: 520px;
    overflow: hidden;
}

.search-box input {
    border: none;
    padding: 12px;
    width: 100%;
}

.search-btn {
    background: #febd69;
    padding: 12px 18px;
    font-weight: bold;
}

.card {
    background: white;
    padding: 15px;
    border-radius: 10px;
    box-shadow: 0px 2px 6px rgba(0,0,0,0.1);
    text-align: center;
    height: 100%;
    display: flex;
    flex-direction: column;
}

.card img {
    border-radius: 8px;
    margin-bottom: 10px;
}

.product-description {
    font-size: 1.2em;
    color: #333;
    margin-top: 8px;
    margin-bottom: 5px;
    line-height: 1.4;
    min-height: 40px;
}

.similarity-score {
    font-size: 1.0em;
    color: #666;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

st.title("Sight Match")

# -----------------------------
# SIDEBAR : Upload / Camera / Query Image
# -----------------------------
with st.sidebar:
    upload = st.file_uploader("Upload product image", type=["jpg", "png", "jpeg"])
    camera = st.camera_input("Use camera")

    query_image = None
    file_obj = None

    if upload:
        query_image = Image.open(upload).convert("RGB")
        file_obj = upload

    elif camera:
        query_image = Image.open(camera).convert("RGB")
        file_obj = camera

    if query_image:
        st.image(query_image, width=250)

# -----------------------------
# MAIN AREA : Top Amazon Search Bar
# -----------------------------
st.markdown(
    """
    <div class="amazon-bar">
        <div class="search-box">
            <input placeholder="What can I help you find today?" disabled />
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------
# MAIN AREA : Results
# -----------------------------
st.subheader("Results")

if file_obj:
    with st.spinner("Searching similar products..."):
        results = search_image(file_obj, top_k=9)

    cols = st.columns(3)
    for i, r in enumerate(results):
        with cols[i % 3]:
            with st.container(border=True, height=390):
                # Display image
                img = Image.open(r[r"path"]).convert("RGB")
                img_resized = img.resize((200, 200), Image.Resampling.LANCZOS)
                st.image(img_resized, width=200, use_container_width=False)
                
                # Display description
                description = r.get("description", "Description not available")
                st.markdown(f'<div class="product-description">{description}</div>', unsafe_allow_html=True)
                
                # Display similarity score
                st.markdown(f'<div class="similarity-score">Similarity: {r["score"]:.2f}</div>', unsafe_allow_html=True)
                
                # Display search link button
                product_url = r.get("url")
                if product_url:
                    st.link_button("🔍 Search on AMAZON", product_url, use_container_width=True)
else:
    st.info("Upload an image or use the camera to start the search.")
