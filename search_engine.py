import json
import numpy as np
from PIL import Image
import faiss
import open_clip
import torch
import io
import urllib.parse
from config import model_name, pretrained


# Load model
model, _, preprocess = open_clip.create_model_and_transforms(
    model_name, pretrained=pretrained
)
device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)

# Load index + paths
index = faiss.read_index(f"visual_search/visual_search-{model_name}-dedup.index")
image_paths = json.load(open(f"paths/paths-{model_name}-dedup.json"))

# Load descriptions if available
descriptions_file = f"descriptions-{model_name}.json"
try:
    descriptions = json.load(open(descriptions_file, encoding="utf-8"))
    print(f"Loaded {len(descriptions)} descriptions")
except FileNotFoundError:
    print(f"Descriptions file not found: {descriptions_file}")
    descriptions = {}

def generate_search_url(description, search_engine="amazon"):
    """Generate a search URL based on product description"""
    # Clean and extract keywords from description
    # Remove common words and take meaningful terms
    stop_words = {'a', 'an', 'the', 'with', 'for', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'of', 'is', 'are', 'was', 'were'}
    words = description.lower().replace(',', '').replace('.', '').split()
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    
    # Take first 5-7 keywords for search
    search_query = " ".join(keywords[:7])
    encoded_query = urllib.parse.quote(search_query)
    
    if search_engine == "amazon":
        return f"https://www.amazon.com/s?k={encoded_query}"
    elif search_engine == "google":
        return f"https://www.google.com/search?tbm=shop&q={encoded_query}"
    elif search_engine == "ebay":
        return f"https://www.ebay.com/sch/i.html?_nkw={encoded_query}"
    else:
        return f"https://www.google.com/search?q={encoded_query}"

def search_image(uploaded_file, top_k=5):

    if isinstance(uploaded_file, (bytes, bytearray)):
        img = Image.open(uploaded_file).convert("RGB")
    else:
        img = Image.open(uploaded_file).convert("RGB")

    # preprocess
    img_tensor = preprocess(img).unsqueeze(0).to(device)

    # encode
    with torch.no_grad():
        emb = model.encode_image(img_tensor).cpu().numpy()
        emb = emb / np.linalg.norm(emb)

    # FAISS search
    D, I = index.search(emb.astype("float32"), top_k)

    results = []
    for rank, idx in enumerate(I[0]):
        path = image_paths[idx].replace('//', '/')
        #description = descriptions.get(path, "Description not available") ## used for windows systems
        description = descriptions.get(path, "Description not available") ## used for Linux systems
        
        # Generate search URL from description
        search_url = generate_search_url(description, search_engine="amazon")
        
        results.append({
            "path": path,
            "score": float(D[0][rank]),
            "description": description,
            "url": search_url
        })

    return results
