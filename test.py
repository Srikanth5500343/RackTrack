import os
import json
from pathlib import Path
from tqdm import tqdm
 
def convert_coco_to_yolo(coco_json_path, image_dir, output_dir):
    with open(coco_json_path, 'r') as f:
        coco_data = json.load(f)
 
    categories = {cat['id']: cat['name'] for cat in coco_data['categories']}
    category_id_map = {cat_id: i for i, cat_id in enumerate(sorted(categories.keys()))}
   
    # Prepare image ID to filename mapping
    images = {img['id']: img['file_name'] for img in coco_data['images']}
   
    # Group annotations by image ID
    annotations_per_image = {}
    for ann in coco_data['annotations']:
        img_id = ann['image_id']
        if img_id not in annotations_per_image:
            annotations_per_image[img_id] = []
        annotations_per_image[img_id].append(ann)
   
    labels_dir = Path(output_dir)
    labels_dir.mkdir(parents=True, exist_ok=True)
 
    for img_id, filename in tqdm(images.items(), desc=f"Converting {coco_json_path}"):
        anns = annotations_per_image.get(img_id, [])
        img_path = Path(image_dir) / filename
        label_path = labels_dir / (Path(filename).stem + ".txt")
 
        with open(label_path, 'w') as f:
            for ann in anns:
                bbox = ann['bbox']  # COCO: [x, y, width, height]
                x, y, w, h = bbox
                cx = x + w / 2
                cy = y + h / 2
 
                # Normalize
                img_width = ann.get('width', 1)
                img_height = ann.get('height', 1)
                for image in coco_data['images']:
                    if image['id'] == img_id:
                        img_width = image['width']
                        img_height = image['height']
                        break
 
                norm_cx = cx / img_width
                norm_cy = cy / img_height
                norm_w = w / img_width
                norm_h = h / img_height
 
                class_id = category_id_map[ann['category_id']]
                f.write(f"{class_id} {norm_cx:.6f} {norm_cy:.6f} {norm_w:.6f} {norm_h:.6f}\n")
 
    return [categories[cat_id] for cat_id in sorted(categories.keys())]
 
# === Apply conversion for each split ===
base_path = "D:/coco"
 
splits = ['train', 'valid', 'test']
all_classes = None
for split in splits:
    image_dir = os.path.join(base_path, split)
    coco_json = os.path.join(base_path, f"{split}_coco/_annotations.coco.json")
    label_output = os.path.join(base_path, f"{split}_labels")
 
    classes = convert_coco_to_yolo(coco_json, image_dir, label_output)
    if all_classes is None:
        all_classes = classes  # save class names for YAML
 
 