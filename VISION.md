# VISION.md — Paraguay Import Cost Calculator (Antigravity Version)

## Project Overview
Streamlit web app for calculating total landed costs of imports into Paraguay.
IAS 2 compliant (capitalised costs vs. tax credits). Multi-language (de/en/es).
Built and maintained by Hermes AI agent via Docker container -> SSH -> Podman host.

## Architecture
```
Container (172.18.0.2)          Host (172.18.0.1)
    |                               |
    |--- SSH (key-based) ---------->| AlmaLinux, Podman
    |   ~/.ssh/id_ed25519           | /home/pasc/antigravity-projects/
    |   hermes-20260520             |   paraguay-calc/          <-- THIS PROJECT
    |                               |     app.py (742 lines)
    |                               |     helpers.py (878 lines)  <-- i18n, HS rules, state, DB
    |                               |     Dockerfile
    |                               |     data/
    |                               |       products_hs.db (176 products)
    |                               |       countries.json
    |                               |       currencies.json
    |                               |     requirements.txt
    |                               |   paraguay-import-calculator/  <-- OLD VERSION
```

## Deployment
- Port: 8501 -> 8501 (container internal)
- Command: `podman run -d --name paraguay-calc -p 8501:8501 --restart unless-stopped paraguay-calc:latest`
- URL: http://localhost:8501 (host), http://172.18.0.1:8501 (container)

## Component Status

- [x] Dockerfile (COPY helpers.py + data/)
- [x] helpers.py: i18n (de/en/es), HS-code authority warnings, state persistence
- [x] helpers.py: DB integration (lookup_hs_product, search_products, list_all_products, get_product_categories)
- [x] app.py: single-product calculator with DB expander
- [x] app.py: multi-product calculator with allocation keys
- [x] products_hs.db: 176 products with HS codes, DAI rates, typical FOB/weight
- [x] Extract calculation functions to helpers.py (calc_single_product, calc_multi_product)
- [x] Fix use_container_width deprecation -> width='stretch'
- [x] Multi-product DB integration (product picker in data_editor)

- [x] HS-Code Autocomplete (4+ digits triggers DB suggestions)
- [x] Multi-product DB Product Picker (add to table with quantity)
- [x] auto-deploy.sh (adapted for paraguay-calc, port 8501)
- [ ] Tests (tests_calculator.py exists in old project)

## Technical Details

### SSH Connection
- Container -> Host: `ssh pasc@172.18.0.1`
- Key: ed25519, comment "hermes-20260520"
- Auth: passwordless (key in host ~/.ssh/authorized_keys)

### Podman Commands
```
# Build
cd /home/pasc/antigravity-projects/paraguay-calc
podman build -t paraguay-calc:latest .

# Deploy
podman stop paraguay-calc && podman rm paraguay-calc
podman run -d --name paraguay-calc -p 8501:8501 --restart unless-stopped paraguay-calc:latest

# Check
podman logs paraguay-calc
podman ps --filter name=paraguay-calc
curl http://localhost:8501/
```

### File Paths
- Project root: /home/pasc/antigravity-projects/paraguay-calc/
- Old project: /home/pasc/antigravity-projects/paraguay-import-calculator/
- SSH key (container): /root/.ssh/id_ed25519

## Session Log
| Date       | Changes                                                   |
| 2026-05-20 | Initial setup: SSH key, project clone                     |
| 2026-05-21 | Dockerfile fix, DB integration, deploy on 8501            |
| 2026-05-21 | DB expander + HS autocomplete in single-product tab        |
| 2026-05-21 | calc_single_product / calc_multi_product extracted        |
| 2026-05-21 | use_container_width fixed, auto-deploy.sh created         |
| 2026-05-21 | Multi-product DB picker, VISION.md created                |
| 2026-05-21 | Code: 655+1142=1797 lines (was 707+770=1477, more modular)|

## Working Notes for Future Sessions
1. SSH via 172.18.0.1 (key already in known_hosts)
2. Write files via base64 encoding to avoid heredoc blocks
3. Syntax check with python3 -m py_compile before rebuild
4. Always rebuild (podman build) after code changes
5. Check logs for errors after deploy
6. Use terminal() in execute_code for multi-step SSH operations