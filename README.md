# GetSourceWeb

Web Source Extractor & Auto-Decode Engine

---

## FITUR

- Auto decode Base64, Hex, URL, Unicode
- Extract CSS, JS, Images, Inline scripts
- Multi-threading for speed
- Detailed statistics
- ZIP archive output
- Interactive menu

---

## INSTALLATION

Termux / Android:
pkg update && pkg upgrade
pkg install python git
git clone https://github.com/Yanto-yanti-source/source-extractor/
cd source-extractor
pip install -r requirements.txt
python getsource.py

Linux / Mac:
sudo apt update && sudo apt install python3 python3-pip git -y
git clone https://github.com/Yanto-yanti-source/source-extractor/
cd source-extractor
pip3 install -r requirements.txt
python3 getsource.py

Windows:
git clone https://github.com/Yanto-yanti-source/source-extractor/
cd source-extractor
pip install -r requirements.txt
python getsource.py

---

## USAGE

Interactive Menu:
python getsource.py

Direct Command:
python getsource.py https://example.com
python getsource.py https://target.com -o ./results
python getsource.py -h
python getsource.py -v

---

## OUTPUT STRUCTURE

source_domain_timestamp/
├── index.html
├── manifest.json
├── css/
│   ├── style.css
│   └── inline_*.css
├── js/
│   ├── script.js
│   └── inline_*.js
└── images/
    └── img_*.{jpg,png,gif,webp}

---

## DEPENDENCIES

requests>=2.31.0
beautifulsoup4>=4.12.0
urllib3>=2.0.0

---

## DISCLAIMER

- Dilarang rename full tanpa ada nama amsX
- Jika ingin share kasih ch: https://whatsapp.com/channel/0029Vb06mTx8F2p6ZFxwaL34
- Gunakan dengan bijak
- Tools ini hanya untuk edukasi dan riset
- Dilarang untuk aktivitas ilegal

---

## GITHUB

https://github.com/Yanto-yanti-source/source-extractor/

---

## DEV

amsX
