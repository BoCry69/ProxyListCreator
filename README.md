<img width="1312" height="911" alt="Bildschirmfoto 2025-09-07 um 03 13 53" src="https://github.com/user-attachments/assets/78e3e066-3a33-4761-8a2e-d1bab1c24800" />
<img width="1312" height="911" alt="Bildschirmfoto 2025-09-07 um 03 14 06" src="https://github.com/user-attachments/assets/5a991632-aeea-4588-bc21-996c70f0b37b" />
<img width="1312" height="911" alt="Bildschirmfoto 2025-09-07 um 03 14 18" src="https://github.com/user-attachments/assets/8ce14fea-4360-4791-a48d-dd9b0969f3ba" />

# Proxy List Creator v1

**Proxy List Creator** is a modern desktop app (Tkinter) for harvesting, validating, filtering, analyzing, and exporting free proxies – all in a sleek purple-black UI.

---

## ✨ Features
- Scrape proxies from multiple public lists (HTTP / HTTPS / SOCKS4 / SOCKS5)  
- Asynchronous validation with progress bars, ETA, and speed stats  
- Filters by **country**, **anonymity** (elite / anonymous / transparent), and **speed** (fast / medium / slow)  
- Analytics: Fast/Medium/Slow counters & global distribution text chart  
- Export results as **TXT**, **CSV**, or **JSON**  
- Local persistence using **SQLite** database  

---

## 🛠 Requirements
- Python **3.10+**  
- Tkinter (bundled with most Python installs, on Linux: `sudo apt install python3-tk`)  
- Python packages:  
  ```bash
  pip install aiohttp
  # optional (for SOCKS proxies)
  pip install aiohttp_socks
