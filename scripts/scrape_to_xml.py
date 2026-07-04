import urllib.request
import json
import re
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import xml.etree.ElementTree as ET
from xml.dom import minidom

def fetch_condo_xml_element(url, headers, retries=2):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=12) as response:
                html = response.read().decode('utf-8')
            
            # Extract SEO description from HTML meta tags
            desc_match = re.search(r'<meta name="description" content="(.*?)"', html, re.IGNORECASE)
            description = desc_match.group(1) if desc_match else ""
            
            # Extract NEXT_DATA JSON
            next_data_match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
            if not next_data_match:
                return None
                
            data = json.loads(next_data_match.group(1).strip())
            condoInfo = data.get('props', {}).get('pageProps', {}).get('condoInfo', {})
            
            if not condoInfo or condoInfo.get('error'):
                return None
            
            # Create XML node for this condominium
            condo_elem = ET.Element("condominio")
            ET.SubElement(condo_elem, "id").text = str(condoInfo.get('hashId', ''))
            ET.SubElement(condo_elem, "slug").text = str(condoInfo.get('slug', ''))
            ET.SubElement(condo_elem, "nome").text = str(condoInfo.get('name', ''))
            ET.SubElement(condo_elem, "descricao").text = description
            
            # Location details
            loc = ET.SubElement(condo_elem, "localizacao")
            ET.SubElement(loc, "endereco").text = str(condoInfo.get('address', ''))
            ET.SubElement(loc, "numero").text = str(condoInfo.get('number', ''))
            ET.SubElement(loc, "cep").text = str(condoInfo.get('zipCode', ''))
            ET.SubElement(loc, "bairro").text = str(condoInfo.get('neighborhood', ''))
            
            city_info = condoInfo.get('city')
            city_name = city_info.get('name', 'Florianópolis') if isinstance(city_info, dict) else 'Florianópolis'
            ET.SubElement(loc, "cidade").text = city_name
            ET.SubElement(loc, "estado").text = "SC"
            ET.SubElement(loc, "latitude").text = str(condoInfo.get('lat', ''))
            ET.SubElement(loc, "longitude").text = str(condoInfo.get('lng', ''))
            
            # Specifications (characteristics)
            specs = ET.SubElement(condo_elem, "caracteristicas")
            ET.SubElement(specs, "area_min").text = str(condoInfo.get('minArea', ''))
            ET.SubElement(specs, "area_max").text = str(condoInfo.get('maxArea', ''))
            ET.SubElement(specs, "quartos_min").text = str(condoInfo.get('minBedrooms', ''))
            ET.SubElement(specs, "quartos_max").text = str(condoInfo.get('maxBedrooms', ''))
            ET.SubElement(specs, "banheiros_min").text = str(condoInfo.get('minBathrooms', ''))
            ET.SubElement(specs, "banheiros_max").text = str(condoInfo.get('maxBathrooms', ''))
            ET.SubElement(specs, "vagas_min").text = str(condoInfo.get('minParkingSlots', ''))
            ET.SubElement(specs, "vagas_max").text = str(condoInfo.get('maxParkingSlots', ''))
            
            # Infrastructure and installations
            est = ET.SubElement(condo_elem, "estrutura")
            ET.SubElement(est, "portaria").text = str(condoInfo.get('features', {}).get('doorman', ''))
            
            itens = ET.SubElement(est, "itens")
            installations = condoInfo.get('features', {}).get('installations', [])
            for inst in installations:
                item_elem = ET.SubElement(itens, "item")
                item_elem.text = inst.get('text', '')
                item_elem.set('disponivel', inst.get('value', ''))
                
            # Image gallery URLs (photos)
            photos_elem = ET.SubElement(condo_elem, "fotos")
            images = condoInfo.get('images', {}).get('items', {})
            for cat, img_list in images.items():
                for img in img_list:
                    filename = img.get('url', '')
                    if not filename:
                        continue
                    full_url = filename if filename.startswith('http') else f"https://quintoandar.com.br/img/xlg/{filename}"
                    photo_elem = ET.SubElement(photos_elem, "foto")
                    photo_elem.text = full_url
                    photo_elem.set('categoria', cat)
                    photo_elem.set('legenda', img.get('subtitle', ''))
                    
            ET.SubElement(condo_elem, "url_original").text = url
            return condo_elem
            
        except Exception as e:
            if attempt == retries - 1:
                print(f"Error fetching/parsing {url}: {e}")
                return None
            time.sleep(1)
    return None

def main():
    base_dir = "/Users/marcelmanduca/.gemini/antigravity-ide/brain/0d1b7fb6-db36-4078-b7e9-63b979ad5e60/scratch/quintoandar_condos"
    txt_path = os.path.join(base_dir, "florianopolis_condos.txt")
    xml_output_path = os.path.join(base_dir, "florianopolis_condos.xml")
    
    if not os.path.exists(txt_path):
        print(f"Error: {txt_path} not found.")
        return
        
    with open(txt_path, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]
        
    print(f"Total URLs to process for XML: {len(urls)}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    root_element = ET.Element("condominios")
    completed = 0
    lock = threading.Lock()
    
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(fetch_condo_xml_element, url, headers): url for url in urls}
        
        for future in as_completed(futures):
            elem = future.result()
            with lock:
                completed += 1
                if elem is not None:
                    root_element.append(elem)
                if completed % 100 == 0:
                    elapsed = time.time() - start_time
                    speed = completed / elapsed if elapsed > 0 else 0
                    print(f"Progress: {completed}/{len(urls)} finished. Appended {len(root_element)} elements. Speed: {speed:.2f} pages/sec")
                    
    # Generate pretty printed XML
    print("Generating XML string and writing to file...")
    raw_xml_str = ET.tostring(root_element, encoding='utf-8')
    
    # Use minidom to pretty print the output
    parsed = minidom.parseString(raw_xml_str)
    pretty_xml_str = parsed.toprettyxml(indent="  ", encoding="utf-8")
    
    with open(xml_output_path, "wb") as f:
        f.write(pretty_xml_str)
        
    print(f"\nXML Generation Complete!")
    print(f"Total condominiums structured: {len(root_element)}")
    print(f"Output XML saved to: {xml_output_path}")

if __name__ == '__main__':
    main()
