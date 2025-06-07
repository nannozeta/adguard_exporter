# 💡AdGuard Exporter

![running script](./assets/targets.png)

Exporter Prometheus untuk mengambil statistik dari AdGuard Home dengan menggunakan Rest API dari AdGuard

### ⚠️ Requirements:
``` 
sudo apt update
sudo apt install python3 python3-pip
pip install requests python-dotenv flask
```

### ✅Cara pakai:

1. Edit .env dan isi sesuai dengan kredential dari AdGuard.
1. Jalankan script: `python3 adguard_exporter.py` dan akses http://localhost:9617 untuk test. 
2. Buat file .env di folder utama, lalu ```sudo cp .env.example .env``` 
4. Gunakan systemd service: `adguard_exporter.service`, jangan lupa update path workdir nya. 
```
sudo cp adguard_exporter.service /etc/systemd/system/
sudo systemctl daemon-reexec
sudo systemctl enable --now adguard_exporter
```

5. Tambahkan di prometheus.yml agar bisa discrape Prometheus.

```
scrape_configs:
  - job_name: 'adguard_exporter'
    static_configs:
      - targets: ['localhost:9617']
``` 
6. Restart prometheus dan akses http://localhost:9090/targets, cek kembali apakah sudah up.
7. Exporter siap digunakan di Grafana

Kali aja ada yang mau donate hehe :)
ETH: ```0x561fa822553e78b25be69e194d271aed5dd202e6```

![Animated](./assets/animated.gif)
