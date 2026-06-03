# VISION.md — Paraguay Import Cost Calculator v4

## Zustand 2026-05-25 20:20

### Laufende Infrastruktur
```
Docker Compose:
  paraguay-calc-db      PostgreSQL 16 (healthy)
  paraguay-calc-app     Streamlit App (Port 8501)
  Volume: pgdata
  Repo: /home/pasc/antigravity-projects/paraguay-calc
```

### GETESTET ÜBERGEBEN — Regel
NIE ungetestet übergeben. Vor jeder Übergabe:
```bash
ssh pasc@172.18.0.1 'curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://127.0.0.1:8501/'
```
Muss `200` sein. Keine Tracebacks, keine Fehlermeldungen.

### Docker-Cache-Falle
Nach Host-Edit der app.py NICHT nur `docker compose up -d` — das cached.
Richtig: `docker compose stop app && docker rm paraguay-calc-app && docker rmi paraguay-calc-app && docker compose build app && docker compose up -d app`

### ✅ Erledigt
- PYG-zentrierte Währung (3 Kurse: FOB, Flete, USD-Referenz)
- Dynamische Recalc (kein Berechnen-Button)
- IVA-Dropdown bei Proveedor (Exento/IVA CF/10%)
- ✕ pro Zeile in allen 4 Tabellen
- HTML-Ergebnis-Tabelle (Ctrl+C kopierbar)
- Sidebar-Navigation: Kalkulator | Mein Verlauf | Admin
- Beispieldaten: 1 Produkt + 3 Produkte

### Dateien
```
├── app.py              (597 Zeilen)
├── calculator.py       (244 Zeilen)
├── database.py         (174 Zeilen)
├── schema.sql
├── docker-compose.yml  (app + db)
├── Dockerfile
├── Dockerfile.db
└── requirements.txt    (streamlit, psycopg2-binary)
```
