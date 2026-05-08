from fastapi import FastAPI, File, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import numpy as np
from PIL import Image
import io
import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TF warnings
import tensorflow as tf

import torch
import torch.nn as nn
from torchvision import models, transforms

import httpx
import json

app = FastAPI(title="Plant Disease Detection API")

# Configure CORS for React frontend (default vite port is 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Paths ──
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
TF_MODEL_PATH = os.path.join(ROOT_DIR, "plant_disease_model.keras")
PT_MODEL_PATH = os.path.join(ROOT_DIR, "plant_disease_model.pth")
PT_SOTA_MODEL_PATH = os.path.join(ROOT_DIR, "plant_disease_model_sota.pth")

# Class names exactly as they appear in the train directory (sorted alphabetically)
CLASS_NAMES = [
    "Apple___Apple_scab",
    "Apple___Black_rot",
    "Apple___Cedar_apple_rust",
    "Apple___healthy",
    "Blueberry___healthy",
    "Cherry_(including_sour)___Powdery_mildew",
    "Cherry_(including_sour)___healthy",
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
    "Corn_(maize)___Common_rust_",
    "Corn_(maize)___Northern_Leaf_Blight",
    "Corn_(maize)___healthy",
    "Grape___Black_rot",
    "Grape___Esca_(Black_Measles)",
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)",
    "Grape___healthy",
    "Orange___Haunglongbing_(Citrus_greening)",
    "Peach___Bacterial_spot",
    "Peach___healthy",
    "Pepper,_bell___Bacterial_spot",
    "Pepper,_bell___healthy",
    "Potato___Early_blight",
    "Potato___Late_blight",
    "Potato___healthy",
    "Raspberry___healthy",
    "Soybean___healthy",
    "Squash___Powdery_mildew",
    "Strawberry___Leaf_scorch",
    "Strawberry___healthy",
    "Tomato___Bacterial_spot",
    "Tomato___Early_blight",
    "Tomato___Late_blight",
    "Tomato___Leaf_Mold",
    "Tomato___Septoria_leaf_spot",
    "Tomato___Spider_mites Two-spotted_spider_mite",
    "Tomato___Target_Spot",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato___Tomato_mosaic_virus",
    "Tomato___healthy"
]

NUM_CLASSES = len(CLASS_NAMES)

# =============================================
#  Helper: build a PyTorch EfficientNetV2-S
# =============================================
def _build_pt_model(weight_path: str):
    """Re-create the EfficientNetV2-S architecture used in training and load state_dict."""
    net = models.efficientnet_v2_s(weights=None)
    num_ftrs = net.classifier[1].in_features
    net.classifier[1] = nn.Sequential(
        nn.Dropout(p=0.3, inplace=True),
        nn.Linear(num_ftrs, NUM_CLASSES),
    )
    state = torch.load(weight_path, map_location="cpu", weights_only=True)
    net.load_state_dict(state)
    net.eval()
    return net

# =============================================
#  Load all models at startup
# =============================================
tf_model = None
pt_model = None
pt_sota_model = None

# TensorFlow / Keras
try:
    print(f"Loading TF model from {TF_MODEL_PATH}")
    tf_model = tf.keras.models.load_model(TF_MODEL_PATH)
    print("TF model loaded successfully")
except Exception as e:
    print(f"Error loading TF model: {e}")

# PyTorch Base
try:
    print(f"Loading PyTorch model from {PT_MODEL_PATH}")
    pt_model = _build_pt_model(PT_MODEL_PATH)
    print("PyTorch model loaded successfully")
except Exception as e:
    print(f"Error loading PyTorch model: {e}")

# PyTorch SOTA
try:
    print(f"Loading PyTorch SOTA model from {PT_SOTA_MODEL_PATH}")
    pt_sota_model = _build_pt_model(PT_SOTA_MODEL_PATH)
    print("PyTorch SOTA model loaded successfully")
except Exception as e:
    print(f"Error loading PyTorch SOTA model: {e}")

# ── PyTorch inference transform (ImageNet stats) ──
pt_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

# =============================================
#  Utilities
# =============================================
def format_class_name(class_name: str) -> str:
    """Make the class name more readable for the UI"""
    return class_name.replace("___", " - ").replace("_", " ")

async def get_llm_advice(disease_name: str) -> dict:
    """Call the local LLM to get prevention and cure advice."""
    url = "http://192.168.1.7:1234/v1/chat/completions"

    prompt = f"The plant has {disease_name}. Provide medium-length advice. Give exactly 2 short bullet points for Prevention and exactly 2 short bullet points for Cure. Maximum 1 sentence per bullet point. Do NOT start with greetings, 'Okay', 'Here is', or any intro/outro filler. Just output the numbered lists."

    payload = {
        "model": "google/gemma-4-26b-a4b",
        "messages": [
            {"role": "system", "content": "You are a professional agricultural expert. Provide concise, actionable advice. Output ONLY the requested bullet points. No conversational text."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 2000
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=60.0)
            response.raise_for_status()
            data = response.json()
            feedback = data["choices"][0]["message"]["content"]
            return {"feedback": feedback}
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return {"error": "Failed to fetch AI advice."}

# =============================================
#  Routes
# =============================================
@app.get("/")
def read_root():
    return {"status": "ok", "message": "Plant Disease Detection API is running"}

@app.get("/models")
def list_models():
    """Return available models so the frontend can populate a selector."""
    available = []
    if tf_model is not None:
        available.append({
            "id": "tensorflow",
            "name": "TensorFlow (Keras)",
            "description": "Custom CNN · ~89% accuracy",
        })
    if pt_model is not None:
        available.append({
            "id": "pytorch",
            "name": "PyTorch (Base)",
            "description": "EfficientNetV2-S · 89.5% accuracy",
        })
    if pt_sota_model is not None:
        available.append({
            "id": "pytorch_sota",
            "name": "PyTorch (SOTA)",
            "description": "EfficientNetV2-S Fine-Tuned · 99.6% accuracy",
        })
    return {"models": available}

@app.post("/predict")
async def predict(
    file: UploadFile = File(...),
    model: str = Query("tensorflow", description="Model to use: tensorflow | pytorch | pytorch_sota"),
):
    # ── Resolve which model to use ──
    if model == "tensorflow":
        active_model = tf_model
    elif model == "pytorch":
        active_model = pt_model
    elif model == "pytorch_sota":
        active_model = pt_sota_model
    else:
        return JSONResponse(status_code=400, content={"error": f"Unknown model '{model}'"})

    if active_model is None:
        return JSONResponse(
            status_code=500,
            content={"error": f"Model '{model}' could not be loaded"},
        )

    try:
        # Read image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")

        if model == "tensorflow":
            # ── TF / Keras inference ──
            image = image.resize((224, 224))
            img_array = np.array(image)
            img_array = np.expand_dims(img_array, axis=0)

            predictions = active_model.predict(img_array)
            predicted_class_idx = int(np.argmax(predictions[0]))
            confidence = float(predictions[0][predicted_class_idx])
        else:
            # ── PyTorch inference ──
            img_tensor = pt_transform(image).unsqueeze(0)  # [1, 3, 224, 224]

            with torch.no_grad():
                outputs = active_model(img_tensor)
                probabilities = torch.nn.functional.softmax(outputs, dim=1)
                confidence, predicted_class_idx = torch.max(probabilities, 1)
                predicted_class_idx = int(predicted_class_idx.item())
                confidence = float(confidence.item())

        predicted_class_name = CLASS_NAMES[predicted_class_idx]
        formatted_name = format_class_name(predicted_class_name)

        response_data = {
            "prediction": predicted_class_name,
            "formatted_prediction": formatted_name,
            "confidence": confidence,
            "model_used": model,
        }

        # If it's not healthy, ask the LLM for advice
        if "healthy" not in predicted_class_name.lower():
            ai_advice = await get_llm_advice(formatted_name)
            response_data["ai_feedback"] = ai_advice

        return response_data

    except Exception as e:
        import traceback
        print("Error during prediction:")
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "traceback": traceback.format_exc()},
        )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# Hot reload trigger to detect python-multipart
