import os
import urllib.request
import xml.etree.ElementTree as ET
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def download_image(url, save_path):
    try:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            with open(save_path, 'wb') as f:
                f.write(response.read())
        return True
    except Exception as e:
        print(f"Error downloading {url} to {save_path}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Download images of Florianópolis condominiums from the generated XML.")
    parser.add_argument("--limit", type=int, default=5, help="Number of condominiums to download images for (default: 5 for testing). Set to 0 for no limit.")
    parser.add_argument("--workers", type=int, default=10, help="Number of parallel download workers (default: 10).")
    args = parser.parse_args()

    # Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    xml_path = os.path.join(project_root, "data", "florianopolis_condos.xml")
    images_dir = os.path.join(project_root, "images")

    if not os.path.exists(xml_path):
        print(f"Error: XML file not found at {xml_path}")
        return

    print("Parsing XML data...")
    tree = ET.parse(xml_path)
    root = tree.getroot()

    condos = root.findall("condominio")
    total_condos = len(condos)
    print(f"Total condominiums in XML: {total_condos}")

    # Apply limits
    limit = args.limit
    if limit > 0:
        condos = condos[:limit]
        print(f"Limiting download to the first {limit} condominiums.")
    else:
        print("Warning: Downloading images for ALL condominiums. This could take a long time and use several Gigabytes of disk space.")

    # Prepare downloads
    downloads = []
    for condo in condos:
        condo_id = condo.find("id").text
        slug = condo.find("slug").text
        fotos = condo.find("fotos").findall("foto")
        
        for idx, foto in enumerate(fotos):
            url = foto.text
            cat = foto.get("categoria", "other")
            save_filename = f"{cat}_{idx + 1}.jpg"
            save_path = os.path.join(images_dir, slug, save_filename)
            downloads.append((url, save_path))

    total_images = len(downloads)
    print(f"Prepared to download {total_images} images.")

    if total_images == 0:
        print("No images found to download.")
        return

    # Start concurrent downloads
    completed = 0
    success_count = 0
    start_time = time.time()
    
    print(f"Downloading images using {args.workers} threads...")
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(download_image, url, path): (url, path) for url, path in downloads}
        for future in as_completed(futures):
            res = future.result()
            completed += 1
            if res:
                success_count += 1
            if completed % 10 == 0 or completed == total_images:
                print(f"Progress: {completed}/{total_images} images processed. Successful: {success_count}")

    elapsed = time.time() - start_time
    print(f"\nDownload finished in {elapsed:.2f} seconds.")
    print(f"Successfully downloaded {success_count} out of {total_images} images.")
    print(f"Images saved to: {images_dir}/")

if __name__ == "__main__":
    main()
