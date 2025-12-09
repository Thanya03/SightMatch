# remove-dup-image.py
import json
import numpy as np
import faiss
from tqdm import tqdm
from config import model_name

def remove_duplicates(similarity_threshold=0.95):
    """
    Remove duplicate images based on embedding similarity.
    
    Args:
        similarity_threshold: Float between 0 and 1. Images with similarity >= threshold are considered duplicates.
                             Default 0.95 means 95% match.
    """
    # Load existing index and paths
    print("Loading existing index and paths...")
    index_path = f"visual_search/visual_search-{model_name}.index"
    paths_file = f"paths/paths-{model_name}.json"
    
    index = faiss.read_index(index_path)
    image_paths = json.load(open(paths_file))
    
    num_vectors = index.ntotal
    dimension = index.d
    print(f"Loaded {num_vectors} embeddings with dimension {dimension}")
    
    # Extract all embeddings from FAISS index
    print("Extracting embeddings from index...")
    embeddings = index.reconstruct_n(0, num_vectors)  # Reconstruct all vectors
    embeddings = np.array(embeddings).astype("float32")
    
    # Normalize embeddings (ensure they're normalized for cosine similarity)
    faiss.normalize_L2(embeddings)
    
    # Create a temporary index for efficient similarity search
    temp_index = faiss.IndexFlatIP(dimension)
    temp_index.add(embeddings)
    
    # Track which indices to keep (True = keep, False = remove)
    keep_mask = np.ones(num_vectors, dtype=bool)
    
    # Find duplicates using FAISS search
    print(f"Finding duplicates with similarity threshold >= {similarity_threshold:.2%}...")
    
    # Search for top-k similar vectors for each embedding
    # We search for top 100 to find potential duplicates
    k = min(100, num_vectors)
    D, I = temp_index.search(embeddings, k)
    
    # Group duplicates
    processed = set()
    duplicates_removed = 0
    
    for i in tqdm(range(num_vectors), desc="Processing embeddings"):
        if not keep_mask[i] or i in processed:
            continue
        
        # Find all similar embeddings above threshold
        similar_indices = []
        for j, similarity in zip(I[i], D[i]):
            if j != i and similarity >= similarity_threshold and keep_mask[j]:
                similar_indices.append(j)
        
        # Mark duplicates for removal (keep the first one, remove others)
        if similar_indices:
            for dup_idx in similar_indices:
                if keep_mask[dup_idx]:
                    keep_mask[dup_idx] = False
                    duplicates_removed += 1
                    processed.add(dup_idx)
        
        processed.add(i)
    
    # Filter embeddings and paths
    print(f"\nRemoved {duplicates_removed} duplicate images")
    print(f"Keeping {keep_mask.sum()} unique images")
    
    unique_embeddings = embeddings[keep_mask]
    unique_paths = [image_paths[i] for i in range(num_vectors) if keep_mask[i]]
    
    # Build new FAISS index
    print("Building new index...")
    new_index = faiss.IndexFlatIP(dimension)
    new_index.add(unique_embeddings)
    
    # Save new index and paths
    new_index_path = f"visual_search/visual_search-{model_name}-dedup.index"
    new_paths_file = f"paths/paths-{model_name}-dedup.json"
    
    faiss.write_index(new_index, new_index_path)
    with open(new_paths_file, "w") as f:
        json.dump(unique_paths, f)
    
    print(f"\nDeduplicated index saved to: {new_index_path}")
    print(f"Deduplicated paths saved to: {new_paths_file}")
    print(f"Original: {num_vectors} images -> Deduplicated: {len(unique_paths)} images")
    print(f"Reduction: {duplicates_removed} images ({duplicates_removed/num_vectors*100:.2f}%)")

if __name__ == "__main__":
    # You can adjust the similarity threshold here
    # 0.95 = 95% match, 0.90 = 90% match, etc.
    similarity_threshold = 0.95  # Change this value as needed
    
    remove_duplicates(similarity_threshold=similarity_threshold)