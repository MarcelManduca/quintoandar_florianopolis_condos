import urllib.request
import xml.etree.ElementTree as ET
import re
import os
import json

def download_and_extract():
    sitemaps = [
        "https://www.quintoandar.com.br/sitemap-v2-condos-v2-part-0000.xml",
        "https://www.quintoandar.com.br/sitemap-v2-condos-v2-part-0001.xml",
        "https://www.quintoandar.com.br/sitemap-v2-condos-v2-part-0002.xml",
        "https://www.quintoandar.com.br/sitemap-v2-condos-v2-part-0003.xml"
    ]
    
    florianopolis_condos = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    for sitemap_url in sitemaps:
        print(f"Fetching {sitemap_url}...")
        try:
            req = urllib.request.Request(sitemap_url, headers=headers)
            with urllib.request.urlopen(req) as response:
                xml_data = response.read()
                
            # Parse XML
            root = ET.fromstring(xml_data)
            
            # The namespace for sitemaps is usually http://www.sitemaps.org/schemas/sitemap/0.9
            namespaces = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            
            count_found = 0
            for url_elem in root.findall('.//ns:loc', namespaces):
                url = url_elem.text
                if not url:
                    continue
                # Normalize and check if it contains florianopolis and condominio
                url_lower = url.lower()
                if '/condominio/' in url_lower and 'florianopolis' in url_lower:
                    florianopolis_condos.append(url)
                    count_found += 1
            print(f"Found {count_found} Florianópolis condominiums in this sitemap.")
            
        except Exception as e:
            print(f"Error processing {sitemap_url}: {e}")
            
    # Save the output to a text file and JSON file
    output_dir = "/Users/marcelmanduca/.gemini/antigravity-ide/brain/0d1b7fb6-db36-4078-b7e9-63b979ad5e60/scratch/quintoandar_condos"
    os.makedirs(output_dir, exist_ok=True)
    
    output_txt = os.path.join(output_dir, "florianopolis_condos.txt")
    output_json = os.path.join(output_dir, "florianopolis_condos.json")
    
    with open(output_txt, "w", encoding="utf-8") as f:
        for url in florianopolis_condos:
            f.write(url + "\n")
            
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(florianopolis_condos, f, indent=4, ensure_ascii=False)
        
    print(f"\nExtraction complete!")
    print(f"Total Florianópolis condominiums found: {len(florianopolis_condos)}")
    print(f"Saved list to {output_txt} and {output_json}")

if __name__ == "__main__":
    download_and_extract()
