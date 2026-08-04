#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║               ░█████╗░███╗░░░███╗░██████╗██╗░░██╗                ║
║               ██╔══██╗████╗░████║██╔════╝╚██╗██╔╝                ║
║               ███████║██╔████╔██║╚█████╗░░╚███╔╝░                ║
║               ██╔══██║██║╚██╔╝██║░╚═══██╗░██╔██╗░                ║
║               ██║░░██║██║░╚═╝░██║██████╔╝██╔╝╚██╗                ║
║               ░░╚═╝╚═╝░░░░░╚═╝╚═════╝░╚═╝░░╚═╝                ║
║                                                                   ║
║              WEB SOURCE EXTRACTOR                                 ║
║                    AUTO DECODE ENGINE                             ║
║                          v1.0.0                                   ║
║                                                                   ║
║                      DEV: amsX                                    ║
║                CREATE BY: amsX                                    ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
"""

import os
import re
import sys
import json
import time
import base64
import urllib.parse
import zipfile
import hashlib
import socket
import ssl
import subprocess
from urllib.parse import urljoin, urlparse
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
    from bs4 import BeautifulSoup
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError as e:
    print(f"\n[!] Missing dependency: {e}")
    print("[*] Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "beautifulsoup4", "urllib3"])
    import requests
    from bs4 import BeautifulSoup
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

VERSION = "1.0.0"
AUTHOR = "amsX"
GITHUB_URL = "https://github.com/amsx/source-extractor"

COLORS = {
    'red': '\033[91m',
    'green': '\033[92m',
    'yellow': '\033[93m',
    'blue': '\033[94m',
    'purple': '\033[95m',
    'cyan': '\033[96m',
    'white': '\033[97m',
    'bold': '\033[1m',
    'reset': '\033[0m'
}

class Decoder:
    
    @staticmethod
    def decode_base64(data):
        try:
            missing_padding = len(data) % 4
            if missing_padding:
                data += '=' * (4 - missing_padding)
            return base64.b64decode(data).decode('utf-8', errors='ignore')
        except:
            return data
    
    @staticmethod
    def decode_hex(data):
        try:
            return bytes.fromhex(data).decode('utf-8', errors='ignore')
        except:
            return data
    
    @staticmethod
    def decode_url(data):
        try:
            return urllib.parse.unquote(data)
        except:
            return data
    
    @staticmethod
    def decode_unicode(data):
        try:
            return data.encode('utf-8').decode('unicode_escape')
        except:
            return data
    
    @classmethod
    def brute_decode(cls, content, max_iter=10):
        if not content or len(content) < 5:
            return content, False
        
        current = content
        decoded = False
        
        for i in range(max_iter):
            changed = False
            
            if re.match(r'^[A-Za-z0-9+/=]+$', current) and len(current) % 4 == 0:
                test = cls.decode_base64(current)
                if test and test != current and len(test) > len(current) * 0.6:
                    current = test
                    changed = True
                    decoded = True
            
            if re.match(r'^[0-9A-Fa-f]+$', current) and len(current) % 2 == 0:
                test = cls.decode_hex(current)
                if test and test != current:
                    current = test
                    changed = True
                    decoded = True
            
            if '%' in current:
                test = cls.decode_url(current)
                if test and test != current:
                    current = test
                    changed = True
                    decoded = True
            
            if '\\u' in current or '\\x' in current:
                test = cls.decode_unicode(current)
                if test and test != current:
                    current = test
                    changed = True
                    decoded = True
            
            if not changed:
                break
        
        return current, decoded


class SourceExtractor:
    
    def __init__(self, url, output_path=None):
        self.target_url = url.rstrip('/')
        self.domain = re.sub(r'[^a-zA-Z0-9]', '_', urlparse(url).netloc)
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if output_path:
            self.output_dir = Path(output_path)
        else:
            self.output_dir = Path(f"source_{self.domain}_{self.timestamp}")
        
        self.setup_session()
        self.files = []
        self.decoded_count = 0
        self.total_size = 0
        self.stats = {
            'html': 0,
            'css': 0,
            'js': 0,
            'images': 0,
            'others': 0
        }
        
        self.visited_urls = set()
        self.max_pages = 50
    
    def setup_session(self):
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=30,
            pool_maxsize=30,
            max_retries=5,
            pool_block=False
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
    
    def fetch(self, url, referer=None):
        if url in self.visited_urls:
            return None
        
        self.visited_urls.add(url)
        
        try:
            if url.startswith('//'):
                url = 'https:' + url
            
            if not url.startswith(('http://', 'https://')):
                url = urljoin(self.target_url, url)
            
            url = url.split('#')[0]
            
            headers = {}
            if referer:
                headers['Referer'] = referer
            
            resp = self.session.get(url, timeout=30, headers=headers, allow_redirects=True)
            resp.raise_for_status()
            
            content_type = resp.headers.get('content-type', '').lower()
            
            if 'text/html' in content_type:
                return resp.text
            elif 'text/css' in content_type:
                return resp.text
            elif 'javascript' in content_type or 'application/javascript' in content_type:
                return resp.text
            elif 'application/json' in content_type:
                return resp.text
            else:
                return resp.content
                
        except Exception as e:
            return None
    
    def save_file(self, filename, content, subdir=''):
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:180] + ext
        
        save_path = self.output_dir / subdir / filename
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        if isinstance(content, bytes):
            with open(save_path, 'wb') as f:
                f.write(content)
            size = len(content)
            is_binary = True
        else:
            content_str = str(content) if content else ''
            with open(save_path, 'w', encoding='utf-8', errors='ignore') as f:
                f.write(content_str)
            size = len(content_str)
            is_binary = False
        
        self.files.append({
            'path': str(save_path),
            'name': filename,
            'size': size,
            'binary': is_binary,
            'decoded': False
        })
        
        self.total_size += size
        
        ext = filename.split('.')[-1].lower() if '.' in filename else 'unknown'
        if ext in ['html', 'htm']:
            self.stats['html'] += 1
        elif ext in ['css']:
            self.stats['css'] += 1
        elif ext in ['js', 'json']:
            self.stats['js'] += 1
        elif ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'ico']:
            self.stats['images'] += 1
        else:
            self.stats['others'] += 1
        
        return save_path
    
    def extract_assets(self, html, base_url):
        if not html:
            return
        
        soup = BeautifulSoup(html, 'html.parser')
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            
            for link in soup.find_all('link', rel='stylesheet'):
                href = link.get('href')
                if href:
                    futures.append(executor.submit(self.process_css, href, base_url))
            
            for script in soup.find_all('script', src=True):
                src = script.get('src')
                if src:
                    futures.append(executor.submit(self.process_js, src, base_url))
            
            for img in soup.find_all('img', src=True):
                src = img.get('src')
                if src:
                    futures.append(executor.submit(self.process_image, src, base_url))
            
            for i, script in enumerate(soup.find_all('script', src=False), 1):
                content = script.string or ''
                if content.strip():
                    self.process_inline_js(content, i)
            
            for i, style in enumerate(soup.find_all('style'), 1):
                content = style.string or ''
                if content.strip():
                    self.process_inline_css(content, i)
            
            for future in as_completed(futures):
                try:
                    future.result(timeout=60)
                except:
                    pass
    
    def process_css(self, href, base_url):
        try:
            css_url = urljoin(base_url, href)
            content = self.fetch(css_url, referer=base_url)
            if content and isinstance(content, str) and len(content) > 5:
                decoded, was_decoded = Decoder.brute_decode(content)
                name = href.split('/')[-1].split('?')[0]
                if not name.endswith('.css'):
                    name += '.css'
                self.save_file(name, decoded, 'css')
                if was_decoded:
                    self.decoded_count += 1
        except:
            pass
    
    def process_js(self, src, base_url):
        try:
            js_url = urljoin(base_url, src)
            content = self.fetch(js_url, referer=base_url)
            if content and isinstance(content, str) and len(content) > 5:
                decoded, was_decoded = Decoder.brute_decode(content)
                name = src.split('/')[-1].split('?')[0]
                if not name.endswith('.js'):
                    name += '.js'
                self.save_file(name, decoded, 'js')
                if was_decoded:
                    self.decoded_count += 1
        except:
            pass
    
    def process_image(self, src, base_url):
        try:
            img_url = urljoin(base_url, src)
            content = self.fetch(img_url)
            if content and isinstance(content, bytes) and len(content) > 100:
                ext = src.split('.')[-1].split('?')[0][:4].lower()
                if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'ico']:
                    ext = 'bin'
                name = f"img_{len(self.files)}.{ext}"
                self.save_file(name, content, 'images')
        except:
            pass
    
    def process_inline_js(self, content, idx):
        try:
            decoded, was_decoded = Decoder.brute_decode(content)
            self.save_file(f"inline_{idx}.js", decoded, 'js')
            if was_decoded:
                self.decoded_count += 1
        except:
            pass
    
    def process_inline_css(self, content, idx):
        try:
            decoded, was_decoded = Decoder.brute_decode(content)
            self.save_file(f"style_{idx}.css", decoded, 'css')
            if was_decoded:
                self.decoded_count += 1
        except:
            pass
    
    def animate_loading(self, message, duration=1):
        chars = ['|', '/', '-', '\\']
        for i in range(duration * 10):
            sys.stdout.write(f'\r{COLORS["cyan"]}[{chars[i % 4]}] {message}{COLORS["reset"]}')
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write('\r' + ' ' * 60 + '\r')
        sys.stdout.flush()
    
    def crawl_and_rip(self):
        print(f"\n{COLORS['cyan']}{'='*60}{COLORS['reset']}")
        print(f"{COLORS['bold']}AMSX SOURCE EXTRACTOR v{VERSION}{COLORS['reset']}")
        print(f"{COLORS['yellow']}TARGET: {self.target_url}{COLORS['reset']}")
        print(f"{COLORS['green']}OUTPUT: {self.output_dir}{COLORS['reset']}")
        print(f"{COLORS['cyan']}{'='*60}{COLORS['reset']}\n")
        
        self.animate_loading("Initializing connection")
        
        print(f"{COLORS['purple']}[>] Connecting to target...{COLORS['reset']}")
        html = self.fetch(self.target_url)
        
        if not html:
            print(f"{COLORS['red']}[X] Connection failed{COLORS['reset']}")
            return False
        
        print(f"{COLORS['green']}[+] Connected successfully ({len(html):,} bytes){COLORS['reset']}")
        
        self.animate_loading("Processing HTML")
        
        decoded_html, was_decoded = Decoder.brute_decode(html)
        self.save_file('index.html', decoded_html)
        
        if was_decoded:
            print(f"{COLORS['green']}[+] HTML decoded{COLORS['reset']}")
        else:
            print(f"{COLORS['yellow']}[!] No encoding detected{COLORS['reset']}")
        
        print(f"{COLORS['purple']}[>] Extracting assets...{COLORS['reset']}")
        
        self.animate_loading("Scanning for CSS files")
        self.extract_assets(decoded_html, self.target_url)
        
        self.create_manifest()
        self.create_zip()
        self.print_summary()
        
        return True
    
    def create_manifest(self):
        manifest = {
            'tool': 'AMSX Source Extractor',
            'version': VERSION,
            'author': AUTHOR,
            'target': self.target_url,
            'domain': self.domain,
            'timestamp': self.timestamp,
            'stats': {
                'total_files': len(self.files),
                'total_size': self.total_size,
                'decoded': self.decoded_count,
                'html': self.stats['html'],
                'css': self.stats['css'],
                'js': self.stats['js'],
                'images': self.stats['images'],
                'others': self.stats['others']
            },
            'files': [
                {
                    'name': f['name'],
                    'size': f['size'],
                    'decoded': f.get('decoded', False)
                } for f in self.files
            ]
        }
        
        with open(self.output_dir / 'manifest.json', 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    def create_zip(self):
        zip_name = f"source_{self.domain}_{self.timestamp}.zip"
        zip_path = Path.cwd() / zip_name
        
        self.animate_loading("Compressing files")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_info in self.files:
                file_path = Path(file_info['path'])
                if file_path.exists():
                    arcname = file_path.relative_to(self.output_dir.parent)
                    zf.write(file_path, arcname)
        
        print(f"{COLORS['green']}[+] Archive created: {zip_name}{COLORS['reset']}")
        return zip_path
    
    def print_summary(self):
        print(f"\n{COLORS['cyan']}{'='*60}{COLORS['reset']}")
        print(f"{COLORS['bold']}{COLORS['green']}EXTRACTION COMPLETE{COLORS['reset']}")
        print(f"{COLORS['cyan']}{'='*60}{COLORS['reset']}")
        print(f"{COLORS['white']}TOTAL FILES : {len(self.files)}{COLORS['reset']}")
        print(f"{COLORS['white']}TOTAL SIZE  : {self.total_size:,} bytes{COLORS['reset']}")
        print(f"{COLORS['white']}DECODED     : {self.decoded_count} files{COLORS['reset']}")
        print(f"{COLORS['cyan']}{'='*60}{COLORS['reset']}")
        print(f"{COLORS['white']}HTML : {self.stats['html']}{COLORS['reset']}")
        print(f"{COLORS['white']}CSS  : {self.stats['css']}{COLORS['reset']}")
        print(f"{COLORS['white']}JS   : {self.stats['js']}{COLORS['reset']}")
        print(f"{COLORS['white']}IMG  : {self.stats['images']}{COLORS['reset']}")
        print(f"{COLORS['white']}OTHER: {self.stats['others']}{COLORS['reset']}")
        print(f"{COLORS['cyan']}{'='*60}{COLORS['reset']}")


def check_environment():
    print(f"{COLORS['purple']}[>] Checking environment...{COLORS['reset']}")
    
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"  {COLORS['white']}Python: {py_version}{COLORS['reset']}")
    
    requirements = ['requests', 'beautifulsoup4', 'urllib3']
    missing = []
    for req in requirements:
        try:
            __import__(req.replace('-', '_'))
            print(f"  {COLORS['green']}[OK] {req}{COLORS['reset']}")
        except:
            print(f"  {COLORS['red']}[X] {req}{COLORS['reset']}")
            missing.append(req)
    
    if missing:
        print(f"\n{COLORS['yellow']}[!] Installing missing packages...{COLORS['reset']}")
        for req in missing:
            subprocess.check_call([sys.executable, "-m", "pip", "install", req])
        print(f"{COLORS['green']}[+] Packages installed{COLORS['reset']}")


def show_help():
    print(f"""
{COLORS['bold']}{COLORS['cyan']}AMSX SOURCE EXTRACTOR v{VERSION}{COLORS['reset']}

{COLORS['yellow']}SYNTAX:{COLORS['reset']}
    python source.py [URL] [OPTIONS]

{COLORS['yellow']}OPTIONS:{COLORS['reset']}
    -o, --output DIR    Output directory
    -h, --help          Show this help
    -v, --version       Show version

{COLORS['yellow']}EXAMPLES:{COLORS['reset']}
    python source.py https://example.com
    python source.py https://target.com -o ./results

{COLORS['yellow']}GITHUB:{COLORS['reset']}
    {GITHUB_URL}
""")


def main():
    if len(sys.argv) >= 2:
        if sys.argv[1] in ['-h', '--help']:
            show_help()
            sys.exit(0)
        elif sys.argv[1] in ['-v', '--version']:
            print(f"AMSX Source Extractor v{VERSION}")
            sys.exit(0)
    
    print(f"""
{COLORS['bold']}╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║               ░█████╗░███╗░░░███╗░██████╗██╗░░██╗                ║
║               ██╔══██╗████╗░████║██╔════╝╚██╗██╔╝                ║
║               ███████║██╔████╔██║╚█████╗░░╚███╔╝░                ║
║               ██╔══██║██║╚██╔╝██║░╚═══██╗░██╔██╗░                ║
║               ██║░░██║██║░╚═╝░██║██████╔╝██╔╝╚██╗                ║
║               ░░╚═╝╚═╝░░░░░╚═╝╚═════╝░╚═╝░░╚═╝                ║
║                                                                   ║
║              WEB SOURCE EXTRACTOR                                 ║
║                    AUTO DECODE ENGINE                             ║
║                          v{VERSION}                                ║
║                                                                   ║
║                      DEV: amsX                                    ║
║                CREATE BY: amsX                                    ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝{COLORS['reset']}
    """)
    
    check_environment()
    
    if len(sys.argv) >= 2 and not sys.argv[1].startswith('-'):
        url = sys.argv[1]
    else:
        print(f"\n{COLORS['yellow']}┌─[TARGET URL]{COLORS['reset']}")
        url = input(f"{COLORS['green']}└─> {COLORS['reset']}").strip()
    
    if not url:
        print(f"{COLORS['red']}[X] No URL provided{COLORS['reset']}")
        sys.exit(1)
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    output = None
    if '-o' in sys.argv or '--output' in sys.argv:
        try:
            idx = sys.argv.index('-o') if '-o' in sys.argv else sys.argv.index('--output')
            output = sys.argv[idx + 1]
        except:
            pass
    
    extractor = SourceExtractor(url, output)
    success = extractor.crawl_and_rip()
    
    if success:
        print(f"\n{COLORS['green']}[+] Extraction completed successfully{COLORS['reset']}")
        print(f"{COLORS['yellow']}GitHub: {GITHUB_URL}{COLORS['reset']}\n")
    else:
        print(f"\n{COLORS['red']}[X] Extraction failed{COLORS['reset']}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{COLORS['yellow']}[!] Process interrupted{COLORS['reset']}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{COLORS['red']}[!] Error: {e}{COLORS['reset']}")
        sys.exit(1)