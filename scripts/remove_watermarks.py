import cv2
import numpy as np
import os
import argparse
import glob

def remove_watermark(img_path, output_path):
    """
    Attempts to remove the translucent white watermark from the center of the image
    using color thresholding and OpenCV inpainting.
    """
    img = cv2.imread(img_path)
    if img is None:
        print(f"Error: Could not read image {img_path}")
        return False
        
    h, w, _ = img.shape
    
    # Create an empty mask
    mask = np.zeros((h, w), dtype=np.uint8)
    
    # QuintoAndar watermarks are typically located in the center of the image.
    # We define a Region of Interest (ROI) in the center (40% width and height).
    cy, cx = h // 2, w // 2
    dy, dx = int(h * 0.20), int(w * 0.20)
    
    # Crop the center region to detect the watermark
    center_roi = img[cy-dy:cy+dy, cx-dx:cx+dx]
    
    # Convert ROI to grayscale
    gray_roi = cv2.cvtColor(center_roi, cv2.COLOR_BGR2GRAY)
    
    # Threshold to detect the bright/white watermark text/logo.
    # White watermarks will have high intensity (e.g., > 230).
    _, thresh_roi = cv2.threshold(gray_roi, 235, 255, cv2.THRESH_BINARY)
    
    # Put the thresholded ROI back into the main mask
    mask[cy-dy:cy+dy, cx-dx:cx+dx] = thresh_roi
    
    # Dilate the mask slightly to cover edges and anti-aliased pixels
    kernel = np.ones((5, 5), np.uint8)
    dilated_mask = cv2.dilate(mask, kernel, iterations=1)
    
    # Apply inpainting (TELEA or NS algorithm)
    result = cv2.inpaint(img, dilated_mask, inpaintRadius=5, flags=cv2.INPAINT_TELEA)
    
    # Save the output image
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, result)
    return True

def main():
    parser = argparse.ArgumentParser(description="Remove watermarks from downloaded condo images.")
    parser.add_argument("--input", type=str, required=True, help="Path to input image or directory of images.")
    parser.add_argument("--output", type=str, required=True, help="Path to save output image or output directory.")
    args = parser.parse_args()

    # Check if input is a directory or a single file
    if os.path.isdir(args.input):
        # Process directory recursively
        image_paths = glob.glob(os.path.join(args.input, "**", "*.jpg"), recursive=True)
        print(f"Found {len(image_paths)} images to process in directory {args.input}")
        
        for idx, img_path in enumerate(image_paths):
            # Maintain directory structure in output
            rel_path = os.path.relpath(img_path, args.input)
            out_path = os.path.join(args.output, rel_path)
            
            print(f"[{idx+1}/{len(image_paths)}] Processing {rel_path}...")
            remove_watermark(img_path, out_path)
    else:
        # Process single file
        print(f"Processing single image: {args.input}")
        remove_watermark(args.input, args.output)
        print(f"Saved cleaned image to: {args.output}")

if __name__ == "__main__":
    main()
