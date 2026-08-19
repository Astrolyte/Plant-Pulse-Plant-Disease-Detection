from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from tensorflow.keras.models import load_model
from PIL import Image
from io import BytesIO
import tensorflow as tf
import numpy as np
import os, uuid, time, batched
import batched


##configuration

MODEL_PATH = "./trained_model_retry.h5"
MAX_FILE_SIZE = 5 * 1024 * 1024
IMAGE_SIZE = (128, 128)
CLASS_NAMES = ["Bacterial_spot", "Early_blight", "Healthy", "Late_blight", "Septoria_leaf_spots", "Yellow_leaf_curl_virus"]

## Flask Application

app = Flask(__name__)
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE

### GPU CONFIGURATION

physical_devices = tf.config.list_physical_devices("GPU")
for device in physical_devices:
    tf.config.experimental.set_memory_growth(device, True)
# --------------------------------------------------
# Dynamic Batching
# --------------------------------------------------

@batched.dynamically(batch_size=8,timeout_ms=20)
def predict_batch(
    image_arrays: list[np.ndarray]
) -> list[np.ndarray]:

    # Combine individual requests into one batch
    input_batch = np.concatenate(image_arrays,axis=0)

    # One GPU inference
    predictions = model.predict(input_batch,verbose=0)

    # batched handles splitting the results
    return predictions


## Load Model

print("Loading Model....")
model = load_model(MODEL_PATH)
print("Model loaded Successfully.")

# Image Preprocessing

def preprocess_image(image_bytes):
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    image = image.resize(IMAGE_SIZE)
    image_array = np.asarray(image, dtype=np.float32)
    image_array = np.expand_dims(image_array, axis=0)
    return image_array

# Health Check

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "PlantPulse API"}), 200

# Readiness Check

@app.route("/api/predict", methods=["POST"])
def predict_disease():
    request_id = str(uuid.uuid4())
    start_time = time.perf_counter()
    try:
        # Validate file existence
        
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded", "request_id": request_id}), 400
        file = request.files["file"]
        
         # Validate filename
         
        if file.filename == "":
            return jsonify({"error": "No file selected", "request_id": request_id}), 400
        
         # Read image into memory
        
        image_bytes = file.read()
        if not image_bytes:
            return jsonify({"error": "Uploaded file is empty", "request_id": request_id}), 400
        
        # Validate image
        
        try:
            input_array = preprocess_image(image_bytes)
        except Exception:
            return jsonify({"error": "Invalid image file", "request_id": request_id}), 400
        
         # Model inference
         
        print("Prediction starting....")
        probabilities = predict_batch(input_array)
        print("prediction done!!")
        
        
        # probabilities = predictions[0]
        
        result_index = int(np.argmax(probabilities))
        confidence = float(probabilities[result_index])
        disease = CLASS_NAMES[result_index]
        
        # Calculate latency
        
        latency_ms = (time.perf_counter() - start_time) * 1000
        
        # Response
        
        return jsonify({
            "request_id": request_id,
            "prediction": {"disease": disease, "confidence": round(confidence, 4)},
            "probabilities": {CLASS_NAMES[i]: round(float(probabilities[i]), 4) for i in range(len(CLASS_NAMES))},
            "metadata": {"model": "PlantPulse-CNN", "image_size": "128x128", "latency_ms": round(latency_ms, 2)}
        }), 200
    except Exception:
        app.logger.exception("Prediction failed | request_id=%s", request_id)
        return jsonify({"error": "Internal prediction error", "request_id": request_id}), 500

# Homepage


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

# Application Entry Point

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)) )