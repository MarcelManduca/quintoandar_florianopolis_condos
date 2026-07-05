import urllib.request
import json
import re
import csv
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

def fetch_condo_rich_data(url, headers, retries=2):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=12) as response:
                html = response.read().decode('utf-8')
            
            # Extract NEXT_DATA JSON
            next_data_match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
            if not next_data_match:
                return None
                
            data = json.loads(next_data_match.group(1).strip())
            condoInfo = data.get('props', {}).get('pageProps', {}).get('condoInfo', {})
            
            if not condoInfo or condoInfo.get('error'):
                return None
            
            # Extract financial fields
            priceValues = condoInfo.get('priceValues') or {}
            negotiatedPriceValues = condoInfo.get('negotiatedPriceValues') or {}
            
            condo_fee = negotiatedPriceValues.get('minCondominium')
            if condo_fee is None:
                condo_fee = priceValues.get('minCondominium')
                
            iptu = negotiatedPriceValues.get('minIptu')
            if iptu is None:
                iptu = priceValues.get('minIptu')
            
            # Prepare rich data dict
            rich_info = {
                'url': url,
                'name': condoInfo.get('name', ''),
                'slug': condoInfo.get('slug', ''),
                'postal_code': condoInfo.get('zipCode', ''),
                'condo_fee_min_brl': condo_fee if condo_fee is not None else '',
                'iptu_min_brl': iptu if iptu is not None else '',
                'area_min_m2': condoInfo.get('minArea') if condoInfo.get('minArea') is not None else '',
                'area_max_m2': condoInfo.get('maxArea') if condoInfo.get('maxArea') is not None else '',
                'bedrooms_min': condoInfo.get('minBedrooms') if condoInfo.get('minBedrooms') is not None else '',
                'bedrooms_max': condoInfo.get('maxBedrooms') if condoInfo.get('maxBedrooms') is not None else '',
                'bathrooms_min': condoInfo.get('minBathrooms') if condoInfo.get('minBathrooms') is not None else '',
                'bathrooms_max': condoInfo.get('maxBathrooms') if condoInfo.get('maxBathrooms') is not None else '',
                'parking_spots_min': condoInfo.get('minParkingSlots') if condoInfo.get('minParkingSlots') is not None else '',
                'parking_spots_max': condoInfo.get('maxParkingSlots') if condoInfo.get('maxParkingSlots') is not None else '',
                'construction_year': condoInfo.get('constructionYear') if condoInfo.get('constructionYear') is not None else ''
            }
            
            return rich_info
            
        except Exception as e:
            if attempt == retries - 1:
                print(f"Error fetching/parsing {url}: {e}")
                return None
            time.sleep(1)
    return None

def main():
    base_dir = "/Users/marcelmanduca/.gemini/antigravity-ide/scratch/quintoandar_florianopolis_condos/data"
    txt_path = os.path.join(base_dir, "florianopolis_condos.txt")
    csv_path = os.path.join(base_dir, "florianopolis_condos_rich.csv")
    
    if not os.path.exists(txt_path):
        print(f"Error: {txt_path} not found.")
        return
        
    with open(txt_path, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]
        
    print(f"Total URLs to scrape for rich data: {len(urls)}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    results = []
    completed = 0
    lock = threading.Lock()
    
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(fetch_condo_rich_data, url, headers): url for url in urls}
        
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
                    
    # Write to CSV
    fields = [
        'url', 'name', 'slug', 'postal_code', 'condo_fee_min_brl', 'iptu_min_brl', 
        'area_min_m2', 'area_max_m2', 'bedrooms_min', 'bedrooms_max', 
        'bathrooms_min', 'bathrooms_max', 'parking_spots_min', 'parking_spots_max', 
        'construction_year'
    ]
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)
        
    print(f"\nScraping complete!")
    print(f"Scraped rich details for {len(results)} condominiums out of {len(urls)}")
    print(f"Rich CSV saved to: {csv_path}")

if __name__ == '__main__':
    main()
