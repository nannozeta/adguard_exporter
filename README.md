# AdGuard Exporter

Exporter Prometheus untuk mengambil statistik dari AdGuard Home dengan menggunakan Rest API dari AdGuard

Prasyarat: 
sudo apt update
sudo apt install python3 python3-pip
pip install requests python-dotenv flask

## Cara pakai

1. Jalankan script: `python3 adguard_exporter.py`
2. Buat file .env di folder utama, lalu ```cp .env.example .env``` 
3. Edit .env dan isi sesuai kredential adguard
4. Gunakan systemd service: `adguard_exporter.service` 
```
sudo cp adguard_exporter.service /etc/systemd/system/
sudo systemctl daemon-reexec
sudo systemctl enable --now adguard_exporter
```

5. Tambahkan di prometheus.yml:

```
scrape_configs:
  - job_name: 'adguard_exporter'
    static_configs:
      - targets: ['localhost:9617']
``` 
6. Restart prometheus dan akses http://localhost:9090/targets, cek kembali apakah sudah up.
7. Exporter siap digunakan di Grafana
