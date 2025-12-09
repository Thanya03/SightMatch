import os
import json
import numpy as np
from PIL import Image
import faiss
import open_clip
import torch
from tqdm import tqdm
from config import model_name, pretrained

# ---------------------------
# 1. Load a stronger OpenCLIP model
# ---------------------------

model, _, preprocess = open_clip.create_model_and_transforms(
    model_name,
    pretrained=pretrained
)

device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)
model.eval()

DATASET_DIR = "dataset"

embeddings = []
image_paths = []

# ---------------------------
# 2. Iterate through dataset and encode images
# ---------------------------
for root, dirs, files in os.walk(DATASET_DIR):
    for file in files:
        if file.lower().endswith((".jpg", ".png", ".jpeg")):
            path = os.path.join(root, file)
            image_paths.append(path)

            img = Image.open(path).convert("RGB")
            img = preprocess(img).unsqueeze(0).to(device)

            with torch.no_grad():
                emb = model.encode_image(img)        # (1, D) torch tensor
                emb = emb / emb.norm(dim=-1, keepdim=True)  # L2 normalize in torch
                emb = emb.cpu().numpy()

            embeddings.append(emb[0])  # (D,)

# ---------------------------
# 3. Stack and build FAISS index
# ---------------------------
embeddings = np.array(embeddings).astype("float32")  # (N, D)

# Build FAISS index (inner product on normalized vectors ≈ cosine similarity)
index = faiss.IndexFlatIP(embeddings.shape[1])
index.add(embeddings)

# ---------------------------
# 4. Save index + paths
# ---------------------------
index_path = f"visual_search/visual_search-{model_name}.index"
faiss.write_index(index, index_path)

with open(f"paths/paths-{model_name}.json", "w") as f:
    json.dump(image_paths, f)

print(f"Index built successfully with {len(image_paths)} images!")
print(f"FAISS index saved to: {index_path}")
