import urllib.request
import json
import re
import csv
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

def fetch_condo_details(url, headers, retries=2):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=12) as response:
                html = response.read().decode('utf-8')
            
            # Find all json-ld scripts
            scripts = re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL)
            
            condo_info = {
                'url': url,
                'name': '',
                'address': '',
                'neighborhood': '',
                'latitude': '',
                'longitude': '',
                'amenities': ''
            }
            
            found_complex = False
            for script_content in scripts:
                try:
                    data = json.loads(script_content.strip())
                    if not isinstance(data, dict):
                        continue
                    
                    if data.get('@type') == 'ApartmentComplex':
                        condo_info['name'] = data.get('name', '')
                        condo_info['address'] = data.get('address', {}).get('streetAddress', '')
                        condo_info['latitude'] = data.get('geo', {}).get('latitude', '')
                        condo_info['longitude'] = data.get('geo', {}).get('longitude', '')
                        
                        amenities_list = [a.get('name') for a in data.get('amenityFeature', []) if a.get('name')]
                        condo_info['amenities'] = '; '.join(amenities_list)
                        found_complex = True
                        
                    elif data.get('@type') == 'BreadcrumbList':
                        items = data.get('itemListElement', [])
                        for item in items:
                            if item.get('position') == 4:
                                name_val = item.get('name', '')
                                # Remove "Condomínios em " prefix
                                if name_val.startswith('Condomínios em '):
                                    name_val = name_val.replace('Condomínios em ', '')
                                condo_info['neighborhood'] = name_val
                                
                except Exception:
                    continue
            
            if found_complex:
                return condo_info
            else:
                return None
                
        except Exception as e:
            if attempt == retries - 1:
                print(f"Error fetching {url}: {e}")
                return None
            time.sleep(1)
    return None

def main():
    base_dir = "/Users/marcelmanduca/.gemini/antigravity-ide/brain/0d1b7fb6-db36-4078-b7e9-63b979ad5e60/scratch/quintoandar_condos"
    txt_path = os.path.join(base_dir, "florianopolis_condos.txt")
    csv_path = os.path.join(base_dir, "florianopolis_condos_detailed.csv")
    
    if not os.path.exists(txt_path):
        print(f"Error: {txt_path} not found.")
        return
        
    with open(txt_path, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]
        
    print(f"Total URLs to scrape: {len(urls)}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    results = []
    completed = 0
    lock = threading.Lock()
    
    # Run requests concurrently using 15 threads to be fast but respect rate limits
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(fetch_condo_details, url, headers): url for url in urls}
        
        for future in as_completed(futures):
            res = future.result()
            with lock:
                completed += 1
                if res:
                    results.append(res)
                if completed % 100 == 0:
                    elapsed = time.time() - start_time
                    speed = completed / elapsed if elapsed > 0 else 0
                    print(f"Progress: {completed}/{len(urls)} finished. Found {len(results)} valid condos. Speed: {speed:.2f} pages/sec")
                    
    # Save results to CSV
    fields = ['url', 'name', 'address', 'neighborhood', 'latitude', 'longitude', 'amenities']
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)
        
    print(f"\nScraping complete!")
    print(f"Successfully scraped details for {len(results)} condominiums out of {len(urls)}")
    print(f"Detailed CSV saved to: {csv_path}")

if __name__ == '__main__':
    main()
