from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import numpy as np
from PIL import Image
import io
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' # Suppress TF warnings
import tensorflow as tf
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

# Load the model
# Assuming main.py is in /backend and model is in the root directory
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plant_disease_model.keras")
model = None

try:
    print(f"Loading model from {MODEL_PATH}")
    model = tf.keras.models.load_model(MODEL_PATH)
    print("Model loaded successfully")
except Exception as e:
    print(f"Error loading model: {e}")

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

def format_class_name(class_name: str) -> str:
    """Make the class name more readable for the UI"""
    return class_name.replace("___", " - ").replace("_", " ")

async def get_llm_advice(disease_name: str) -> dict:
    """Call the local LLM to get prevention and cure advice."""
    url = "http://10.14.189.215:1234/v1/chat/completions"
    
    prompt = f"The plant has {disease_name}. Provide medium-length advice. Give exactly 2 short bullet points for Prevention and exactly 2 short bullet points for Cure. Maximum 1 sentence per bullet point. Do NOT start with greetings, 'Okay', 'Here is', or any intro/outro filler. Just output the numbered lists."
    
    payload = {
        "model": "google/gemma-3-4b",
        "messages": [
            {"role": "system", "content": "You are a professional agricultural expert. Provide concise, actionable advice. Output ONLY the requested bullet points. No conversational text."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 500
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

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Plant Disease Detection API is running"}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if model is None:
        return JSONResponse(
            status_code=500,
            content={"error": "Model could not be loaded"}
        )

    try:
        # Read image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # Preprocess image
        # The model expects an input shape of 224x224
        image = image.resize((224, 224)) 
        img_array = np.array(image)
        
        # Ensure it's the right shape and scale if needed (assuming model handles scaling internally or expects 0-255)
        # Note: Depending on training, you might need img_array = img_array / 255.0
        # Let's try without scaling first, or let's just stick to what Keras model predicts
        
        img_array = np.expand_dims(img_array, axis=0) # Add batch dimension
        
        # Predict
        predictions = model.predict(img_array)
        predicted_class_idx = np.argmax(predictions[0])
        confidence = float(predictions[0][predicted_class_idx])
        
        predicted_class_name = CLASS_NAMES[predicted_class_idx]
        formatted_name = format_class_name(predicted_class_name)
        
        response_data = {
            "prediction": predicted_class_name,
            "formatted_prediction": formatted_name,
            "confidence": confidence
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
            content={"error": str(e), "traceback": traceback.format_exc()}
        )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# Hot reload trigger to detect python-multipart
