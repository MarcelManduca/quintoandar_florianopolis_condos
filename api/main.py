import io
import cv2
import numpy as np
import httpx
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

app = FastAPI(
    title="QuintoAndar Watermark Removal API",
    description="API for removing watermarks from Florianópolis condo images in-memory.",
    version="1.0.0"
)

class ImageURLRequest(BaseModel):
    url: str

def remove_watermark_from_bytes(image_bytes: bytes) -> bytes:
    """
    Decodes the image from bytes, applies color thresholding & inpainting
    to remove the central watermark, and encodes it back to JPEG bytes.
    """
    # Decode bytes to OpenCV image (numpy array)
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image bytes. Verify that the file is a valid image.")
        
    h, w, _ = img.shape
    
    # Create empty mask
    mask = np.zeros((h, w), dtype=np.uint8)
    
    # QuintoAndar watermarks are typically located in the center.
    # Define a Region of Interest (ROI) in the center (40% width and height).
    cy, cx = h // 2, w // 2
    dy, dx = int(h * 0.20), int(w * 0.20)
    
    # Crop the center region to detect the watermark
    center_roi = img[cy-dy:cy+dy, cx-dx:cx+dx]
    
    # Convert ROI to grayscale
    gray_roi = cv2.cvtColor(center_roi, cv2.COLOR_BGR2GRAY)
    
    # Threshold to detect the bright/white watermark text/logo (intensity > 235)
    _, thresh_roi = cv2.threshold(gray_roi, 235, 255, cv2.THRESH_BINARY)
    
    # Put the thresholded ROI back into the main mask
    mask[cy-dy:cy+dy, cx-dx:cx+dx] = thresh_roi
    
    # Dilate the mask slightly to cover anti-aliasing edges
    kernel = np.ones((5, 5), np.uint8)
    dilated_mask = cv2.dilate(mask, kernel, iterations=1)
    
    # Apply inpainting (TELEA)
    result = cv2.inpaint(img, dilated_mask, inpaintRadius=5, flags=cv2.INPAINT_TELEA)
    
    # Encode result back to JPEG bytes
    success, encoded_img = cv2.imencode('.jpg', result)
    if not success:
        raise ValueError("Failed to encode processed image back to JPEG format.")
        
    return encoded_img.tobytes()

@app.get("/")
async def health_check():
    """
    Health check endpoint returning API status.
    """
    return {
        "status": "online",
        "service": "QuintoAndar Watermark Removal API",
        "endpoints": {
            "/clean-image": "POST (Multipart File Upload)",
            "/clean-image-url": "POST (JSON: { 'url': '...' })"
        }
    }

@app.post("/clean-image")
async def clean_image(file: UploadFile = File(...)):
    """
    Upload an image file to remove the central QuintoAndar watermark.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")
        
    try:
        image_bytes = await file.read()
        cleaned_bytes = remove_watermark_from_bytes(image_bytes)
        return StreamingResponse(io.BytesIO(cleaned_bytes), media_type="image/jpeg")
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.post("/clean-image-url")
async def clean_image_url(request: ImageURLRequest):
    """
    Pass an image URL to download it and remove the central QuintoAndar watermark.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(request.url, follow_redirects=True)
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail=f"Failed to fetch image from URL. Status code: {response.status_code}")
            image_bytes = response.content
            
        cleaned_bytes = remove_watermark_from_bytes(image_bytes)
        return StreamingResponse(io.BytesIO(cleaned_bytes), media_type="image/jpeg")
    except httpx.RequestError as re:
        raise HTTPException(status_code=400, detail=f"HTTP request to image URL failed: {str(re)}")
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
