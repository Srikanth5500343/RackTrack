import numpy as np
import pandas as pd
import faiss
import pickle
import os
import sys

# --- Input Args ---
if len(sys.argv) != 6:
    print("Usage: python comparision.py <catalog_path> <cropped_path> <metadata_path> <csv_output_path> <html_output_path>")
    sys.exit(1)

catalog_path = sys.argv[1]
cropped_path = sys.argv[2]
metadata_path = sys.argv[3]
csv_output_path = sys.argv[4]
html_output_path = sys.argv[5]

top_k = 1

# --- Load Data ---
print("[INFO] Loading catalog, cropped embeddings, and metadata...")

with open(catalog_path, "rb") as f:
    catalog_data = pickle.load(f)

with open(cropped_path, "rb") as f:
    cropped_data = pickle.load(f)

metadata = pd.read_pickle(metadata_path)

# --- Normalize for cosine similarity ---
def l2_normalize(x):
    return x / np.linalg.norm(x, axis=1, keepdims=True)

# --- Results Container ---
results = []

# --- Matching per Category ---
categories = set(cropped_data.keys()) & set(catalog_data.keys())
print(f"[INFO] Matching for categories: {sorted(categories)}")

for category in sorted(categories):
    print(f"[INFO] Processing category: {category}")

    crop_embeds = cropped_data[category]["image_embeddings"]
    crop_paths = cropped_data[category]["image_paths"]

    cat_embeds = catalog_data[category]["image_embeddings"]

    crop_embeds = l2_normalize(crop_embeds)
    cat_embeds = l2_normalize(cat_embeds)

    dim = cat_embeds.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(cat_embeds)

    distances, indices = index.search(crop_embeds, top_k)

    for i, (idx_list, dist_list) in enumerate(zip(indices, distances)):
        for idx, score in zip(idx_list, dist_list):
            meta_row = metadata[category].iloc[idx]
            # Fix the image paths to be relative web paths
            cropped_img_path = crop_paths[i]
            
            # Convert Windows-style absolute path to web-friendly relative path
            # Example: "e:\UI\static\segmented_outputs\Cable\file.jpg" -> "/static/segmented_outputs/Cable/file.jpg"
            if 'segmented_outputs' in cropped_img_path:
                # Extract the path after "segmented_outputs"
                parts = cropped_img_path.split('segmented_outputs')
                if len(parts) > 1:
                    cropped_img_path = '/static/segmented_outputs' + parts[1].replace('\\', '/')
                else:
                    # For fallback, convert backslashes to forward slashes
                    cropped_img_path = cropped_img_path.replace('\\', '/')
                    # If starts with drive letter, extract just the filename
                    if ':' in cropped_img_path:
                        cropped_img_path = '/' + '/'.join(cropped_img_path.split('/')[-3:])
            
            # Same for catalog images if they exist
            matched_img = meta_row['Image']
            if isinstance(matched_img, str) and 'static' in matched_img:
                matched_img = '/' + matched_img.split('static', 1)[1].replace('\\', '/')
            
            result = {
                'cropped_image': cropped_img_path,
                'category': category,
                'name': meta_row['Name'],
                'description': meta_row['Description'],
                'matched_image': matched_img,
                'image_path': cropped_img_path, 
                'similarity_score': float(score)
            }
            results.append(result)

# --- Assemble DataFrame ---
df = pd.DataFrame(results)
df = df.drop_duplicates(subset=['matched_image', 'category'])

# For HTML image rendering
def path_to_img_html(path):
    # The path in the CSV is a web path (starting with /static/...)
    # For checking existence, we need to remove the leading slash and check relative to the base dir
    if path.startswith('/'):
        # Convert web path to file system path for existence check
        file_path = path[1:]  # Remove leading slash
    else:
        file_path = path
        
    # Use the web path in the HTML regardless of existence
    return f'<img src="{path}" width="100" onerror="this.onerror=null; this.src=\'/static/images/image-not-found.svg\'; this.alt=\'Image not found\'"/>'

df['Cropped Image'] = df['cropped_image'].apply(path_to_img_html)
df['Matched Catalog Image'] = df['matched_image'].apply(path_to_img_html)

# --- Save CSV and HTML ---
df.to_csv(csv_output_path, index=False)

df_display = df[[
    'cropped_image', 'category', 'name', 'description', 
    'matched_image', 'image_path', 'similarity_score'
]]

df_display.to_html(html_output_path, escape=False, index=False)

print(f"✅ Matching complete. Results saved to:")
print(f"    → CSV : {csv_output_path}")
print(f"    → HTML: {html_output_path}")
