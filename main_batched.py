from io import BytesIO
import hashlib
import json
import os
import time
import uuid

import batched
import numpy as np
import redis
import tensorflow as tf
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from PIL import Image
from tensorflow.keras.models import load_model


# Configuration

MODEL_PATH = "./trained_model_retry.h5"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
IMAGE_SIZE = (128, 128)

CLASS_NAMES = [
    "Bacterial_spot",
    "Early_blight",
    "Healthy",
    "Late_blight",
    "Septoria_leaf_spots",
    "Yellow_leaf_curl_virus",
]

# Redis configuration

REDIS_HOST = "localhost"
REDIS_PORT = 6379
CACHE_TTL = 3600  # 1 hour
MODEL_VERSION = "v1"


# Flask Application

app = Flask(__name__)
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE


# GPU Configuration


physical_devices = tf.config.list_physical_devices("GPU")

for device in physical_devices:
    tf.config.experimental.set_memory_growth(device, True)


# Load Model


print("Loading Model....")
model = load_model(MODEL_PATH)
print("Model loaded Successfully.")


# Redis Connection

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,
    socket_connect_timeout=1,
    socket_timeout=1,
)

# Redis Connection Test

try:
    redis_client.ping()
    print("Redis connected successfully.")
except redis.RedisError as e:
    print(f"WARNING: Redis unavailable: {e}")
    print("PlantPulse will continue without caching.")

# Cache Key

def generate_cache_key(image_bytes):
    image_hash = hashlib.sha256(image_bytes).hexdigest()

    return f"plantpulse:{MODEL_VERSION}:prediction:{image_hash}"

# Image Preprocessing

def preprocess_image(image_bytes):
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    image = image.resize(IMAGE_SIZE)

    image_array = np.asarray(image, dtype=np.float32)
    image_array = np.expand_dims(image_array, axis=0)

    return image_array

# Dynamic Batching

@batched.dynamically(batch_size=8, timeout_ms=20)
def predict_batch(image_arrays: list[np.ndarray]) -> list[np.ndarray]:
    input_batch = np.concatenate(image_arrays, axis=0)
    predictions = model.predict(input_batch, verbose=0)

    return predictions

# Health Check

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "PlantPulse API",
    }), 200


# Prediction Endpoint

@app.route("/api/predict", methods=["POST"])
def predict_disease():
    request_id = str(uuid.uuid4())
    start_time = time.perf_counter()

    try:
        
        # Validate file existence

        if "file" not in request.files:
            return jsonify({
                "error": "No file uploaded",
                "request_id": request_id,
            }), 400

        file = request.files["file"]
        
        # Validate filename

        if file.filename == "":
            return jsonify({
                "error": "No file selected",
                "request_id": request_id,
            }), 400

        # Read image into memory

        image_bytes = file.read()

        if not image_bytes:
            return jsonify({
                "error": "Uploaded file is empty",
                "request_id": request_id,
            }), 400

        # Generate cache key
        cache_key = generate_cache_key(image_bytes)

        # REDIS CACHE LOOKUP
        
        cache_hit = False

        try:
            cached_result = redis_client.get(cache_key)
        except redis.RedisError as e:
            cached_result = None
            app.logger.warning(
                "Redis GET failed | request_id=%s | error=%s",
                request_id,
                e,
            )

        # CACHE HIT
    
        if cached_result is not None:
            cache_hit = True
            result = json.loads(cached_result)
            latency_ms = (time.perf_counter() - start_time) * 1000

            result["request_id"] = request_id
            result["metadata"]["cache_hit"] = True
            result["metadata"]["latency_ms"] = round(latency_ms, 2)
            print(
                f"[CACHE HIT] "
                f"request_id={request_id} "
                f"latency={latency_ms:.2f} ms"
            )
            return jsonify(result), 200
        
            

        # CACHE MISS
        print(f"[CACHE MISS] " f"request_id={request_id}")
        
        
        # Image preprocessing
    
        try:
            input_array = preprocess_image(image_bytes)
        except Exception:
            return jsonify({
                "error": "Invalid image file",
                "request_id": request_id,
            }), 400
        
        # Dynamic Batched Inference
        
        print(f"Prediction starting.... request_id={request_id}")
        prediction = predict_batch(input_array)
        print(f"Prediction done!! request_id={request_id}")

        print(
            f"[INFERENCE] "
            f"request_id={request_id}"
        )
        # Extract prediction
        

        probabilities = prediction

        result_index = int(np.argmax(probabilities))
        confidence = float(probabilities[result_index])
        disease = CLASS_NAMES[result_index]
        
        
        
        # Calculate latency
        
        latency_ms = (time.perf_counter() - start_time) * 1000
        
        # Build Result
        

        result = {
            "prediction": {
                "disease": disease,
                "confidence": round(confidence, 4),
            },
            "probabilities": {
                CLASS_NAMES[i]: round(float(probabilities[i]), 4)
                for i in range(len(CLASS_NAMES))
            },
            "metadata": {
                "model": "PlantPulse-CNN",
                "image_size": "128x128",
                "latency_ms": round(latency_ms, 2),
                "cache_hit": False,
            },
        }
        
        # STORE RESULT IN REDIS    

        try:
            redis_client.set(cache_key, json.dumps(result), ex = CACHE_TTL)
        except redis.RedisError as e:
            # Redis failure must NOT break
            # the prediction request.
            app.logger.warning(
                "Redis SET failed | request_id=%s | error=%s",
                request_id,
                e,
            )
            print(
                f"[CACHE SET] "
                f"request_id={request_id}"
            )
        
        # Add request ID  

        result["request_id"] = request_id
   
        # Response
     

        return jsonify(
            result,
        ), 200

    # Unexpected Error

    except Exception:
        
        app.logger.exception(
            "Prediction failed | request_id=%s",
            request_id
        )
        
        return jsonify({
            "error": "Internal prediction error",
            "request_id": request_id,
        }), 500

# Homepage

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

# Application Entry Point

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
    )