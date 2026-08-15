# # from flask import Flask, request, jsonify, send_file
# # from flask_cors import CORS
# # import cv2
# # import tensorflow as tf
# # from tensorflow import keras
# # from tensorflow.keras.models import load_model 
# # from tensorflow.keras.preprocessing.image import load_img, img_to_array
# # import numpy as np
# # import os
# # from io import BytesIO

# # app = Flask(__name__)
# # CORS(app)

# # physical_devices = tf.config.list_physical_devices('GPU')
# # for device in physical_devices:
# #     tf.config.experimental.set_memory_growth(device, True)
    
# # # model_path = r'C:\Users\Aditya\Documents\Minor_Project\Tomato\trained_model_retry.h5'
# # model_path = './trained_model_retry.h5'
# # model = load_model(model_path)

# # class_names = [
# #     'Bacterial_spot', 'Early_blight', 'Healthy', 'Late_blight', 'Septoria_leaf_spots', 'Yellow_leaf_curl_virus'
# # ]

# # def preprocess_image(image_path):
# #     """
# #     Reads an image from the given path, preprocesses it for the model,
# #     and returns both the original image and preprocessed array.
# #     """
# #     img = cv2.imread(image_path)
# #     img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
# #     image = tf.keras.preprocessing.image.load_img(image_path, target_size=(128, 128)) 
# #     input_arr = tf.keras.preprocessing.image.img_to_array(image)  
# #     input_arr = np.array([input_arr]) 
# #     return img, input_arr

# # @app.route('/api/predict', methods=['POST'])
# # def predict_disease():
# #     try:
# #         if 'file' not in request.files:
# #             return jsonify({"error": "No file part"}), 400

# #         file = request.files['file']
# #         if file.filename == '':
# #             return jsonify({"error": "No selected file"}), 400

# #         file_path = f"./temp_{file.filename}"
# #         file.save(file_path)

# #         img, input_arr = preprocess_image(file_path)

# #         predictions = model.predict(input_arr)
# #         result_index = np.argmax(predictions)
# #         model_prediction = class_names[result_index]

# #         os.remove(file_path)

# #         return jsonify({
# #             "disease": model_prediction,
# #             "probabilities": predictions.flatten().tolist()
# #         })

# #     except Exception as e:
# #         return jsonify({"error": str(e)}), 500

# # if __name__ == "__main__":
# #     app.run(host='0.0.0.0', port=5000)

# # BREAKKKKKKKKKKKKKKKKK



from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import cv2
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import load_img, img_to_array
import numpy as np
import os
from io import BytesIO

app = Flask(__name__)
CORS(app)

physical_devices = tf.config.list_physical_devices('GPU')
for device in physical_devices:
    tf.config.experimental.set_memory_growth(device, True)

model_path = './trained_model_retry.h5'
model = load_model(model_path)

class_names = [
    'Bacterial_spot', 'Early_blight', 'Healthy', 'Late_blight', 'Septoria_leaf_spots', 'Yellow_leaf_curl_virus'
]

def preprocess_image(image_path):
    img = cv2.imread(image_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    image = tf.keras.preprocessing.image.load_img(image_path, target_size=(128, 128)) 
    input_arr = tf.keras.preprocessing.image.img_to_array(image)  
    input_arr = np.array([input_arr]) 
    return img, input_arr

@app.route('/')
def index():
    return render_template('index.html')  # This will serve your HTML file

@app.route('/api/predict', methods=['POST'])
def predict_disease():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        file_path = f"./temp_{file.filename}"
        file.save(file_path)

        img, input_arr = preprocess_image(file_path)

        predictions = model.predict(input_arr)
        result_index = np.argmax(predictions)
        model_prediction = class_names[result_index]

        os.remove(file_path)

        return jsonify({
            "disease": model_prediction,
            "probabilities": predictions.flatten().tolist()
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
