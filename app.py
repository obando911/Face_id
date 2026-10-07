from flask import Flask, render_template, request, jsonify
import os
os.environ["TF_USE_LEGACY_KERAS"] = "1"

import tf_keras
import numpy as np
from PIL import Image, ImageOps
import base64
from io import BytesIO

app = Flask(__name__)

# Cargar modelo
MODEL_PATH = os.path.join("model", "keras_model.h5")
model = tf_keras.models.load_model(MODEL_PATH, compile=False)

# Cargar índice faceId -> nombre
face_index = {}
with open(os.path.join("model", "labels.txt"), "r") as f:
    for line in f:
        parts = line.strip().split(" ", 1)
        face_index[int(parts[0])] = parts[1]

UMBRAL_CONFIANZA = 50
MARGEN_MINIMO = 15


def preprocesar_imagen(image_data_url):
    # Quitar el encabezado "data:image/jpeg;base64,"
    header, encoded = image_data_url.split(",", 1)
    img_bytes = base64.b64decode(encoded)
    image = Image.open(BytesIO(img_bytes)).convert("RGB")
    image = ImageOps.fit(image, (224, 224), Image.Resampling.LANCZOS)
    image_array = np.asarray(image)
    normalized = (image_array.astype(np.float32) / 127.5) - 1
    data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
    data[0] = normalized
    return data


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    body = request.get_json()
    image_data_url = body.get("image")

    data = preprocesar_imagen(image_data_url)
    prediction = model.predict(data, verbose=0)[0]

    orden = np.argsort(prediction)[::-1]
    id_1, id_2 = int(orden[0]), int(orden[1])
    conf_1 = float(prediction[id_1] * 100)
    conf_2 = float(prediction[id_2] * 100)
    margen = conf_1 - conf_2
    nombre = face_index[id_1]

    acceso = conf_1 >= UMBRAL_CONFIANZA and margen >= MARGEN_MINIMO

    top3 = [
        {"nombre": face_index[int(i)], "confianza": float(prediction[i] * 100)}
        for i in orden[:3]
    ]

    return jsonify({
        "acceso": acceso,
        "face_id": id_1,
        "nombre": nombre,
        "confianza": round(conf_1, 2),
        "margen": round(margen, 2),
        "top3": top3
    })


if __name__ == "__main__":
    # ssl_context='adhoc' habilita HTTPS, necesario para que el celular permita la cámara
    app.run(host="0.0.0.0", port=5000, ssl_context="adhoc", debug=True)