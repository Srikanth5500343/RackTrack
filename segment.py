import os
import cv2
import sys
from ultralytics import YOLO

# --- Configuration ---
GENERAL_MODEL_PATH = r"best.pt"  # For Cable, Switch, Rack, fuse
PORTS_MODEL_PATH = r"port_best.pt"  # For Ports
OUTPUT_DIR = r"static/segmented_outputs"
CONF_THRESHOLD = 0.1

# --- Input Image from Command Line ---
if len(sys.argv) < 2:
    print("❌ Please provide input image path.")
    sys.exit(1)

IMAGE_PATH = sys.argv[1]

# --- Read Image ---
img = cv2.imread(IMAGE_PATH)
if img is None:
    raise FileNotFoundError(f"Image not found: {IMAGE_PATH}")

# --- Define Class to Folder Mapping ---
TARGET_CLASS_MAP = {
    'Cable': 'Cable',
    'Port': 'Port', 
    'Rack': 'Rack',
    'Switch': 'Switch',
    'fuse': 'Rack'  # Treat 'fuse' as Rack
}

# --- Create Output Folders ---
for folder in set(TARGET_CLASS_MAP.values()):
    class_dir = os.path.join(OUTPUT_DIR, folder)
    os.makedirs(class_dir, exist_ok=True)

print(f"🧠 Processing image: {IMAGE_PATH}")

# --- Step 1: Run General Model for Cable, Switch, Rack, fuse ---
print(f"📦 Loading general model from: {GENERAL_MODEL_PATH}")
general_model = YOLO(GENERAL_MODEL_PATH)
general_model.overrides['conf'] = CONF_THRESHOLD
general_model.overrides['data'] = None
general_model.overrides['source'] = IMAGE_PATH

general_results = general_model(img, verbose=True)[0]
general_class_names = general_model.names
print(f"📚 General model class names: {general_class_names}")

# --- Step 2: Run Ports Model for Port detection ---
print(f"📦 Loading ports model from: {PORTS_MODEL_PATH}")
ports_model = YOLO(PORTS_MODEL_PATH)
ports_model.overrides['conf'] = CONF_THRESHOLD
ports_model.overrides['data'] = None
ports_model.overrides['source'] = IMAGE_PATH

ports_results = ports_model(img, verbose=True)[0]
ports_class_names = ports_model.names
print(f"📚 Ports model class names: {ports_class_names}")

# --- Process General Model Results ---
print("\n📊 Processing general model detections:")
object_counter = 0

for i, (box, cls_id, conf) in enumerate(zip(general_results.boxes.xyxy, general_results.boxes.cls, general_results.boxes.conf)):
    class_id = int(cls_id)
    confidence = float(conf)
    class_name = general_class_names.get(class_id, f"Unknown_{class_id}")

    print(f"  #{object_counter}: {class_name} (ID: {class_id}, Confidence: {confidence:.2f})")

    # Only process Cable, Switch, Rack, fuse (not Port)
    if class_name in ['Cable', 'Switch', 'Rack', 'fuse']:
        # --- Crop Detected Region ---
        x1, y1, x2, y2 = map(int, box)
        crop = img[y1:y2, x1:x2]

        # --- Save Cropped Image ---
        folder_name = TARGET_CLASS_MAP[class_name]
        crop_filename = f"{os.path.splitext(os.path.basename(IMAGE_PATH))[0]}_{class_name}_{object_counter}.jpg"
        crop_path = os.path.join(OUTPUT_DIR, folder_name, crop_filename)
        cv2.imwrite(crop_path, crop)
        print(f"✅ Saved: {crop_path}")
    else:
        print(f"  ⏩ Skipping {class_name} (handled by ports model)")
    
    object_counter += 1

# --- Process Ports Model Results ---
print("\n📊 Processing ports model detections:")

for i, (box, cls_id, conf) in enumerate(zip(ports_results.boxes.xyxy, ports_results.boxes.cls, ports_results.boxes.conf)):
    class_id = int(cls_id)
    confidence = float(conf)
    class_name = ports_class_names.get(class_id, f"Unknown_{class_id}")

    print(f"  #{object_counter}: {class_name} (ID: {class_id}, Confidence: {confidence:.2f})")

    # Only process Port detections
    if class_name == 'Port' or 'port' in class_name.lower():
        # --- Crop Detected Region ---
        x1, y1, x2, y2 = map(int, box)
        crop = img[y1:y2, x1:x2]

        # --- Save Cropped Image ---
        crop_filename = f"{os.path.splitext(os.path.basename(IMAGE_PATH))[0]}_Port_{object_counter}.jpg"
        crop_path = os.path.join(OUTPUT_DIR, 'Port', crop_filename)
        cv2.imwrite(crop_path, crop)
        print(f"✅ Saved: {crop_path}")
    else:
        print(f"  ⏩ Skipping {class_name} (not a port)")
    
    object_counter += 1

print(f"\n✅ Segmentation and cropping completed for: {IMAGE_PATH}")
print(f"📈 Total objects detected: {object_counter}")
