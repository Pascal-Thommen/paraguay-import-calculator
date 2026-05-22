# Paraguay Import Calculator — Sprint-Plan 2026-05-22

> Pascal's Vision: professioneller, mehrsprachiger Import-Kostenrechner (IAS 2, Ley 6380/19)

## Done
- [x] 0.5% Valoracion CIF fix (gesetzlich festgelegt, Radio entfernt)
- [x] Reset-Button gefixt (use_container_width)
- [x] calc_single_product + calc_multi_product in helpers.py extrahiert
- [x] 12/12 pytest Tests grun
- [x] Mobile-CSS @480px (single-column, full-width inputs, touch targets 44px)
- [x] Excel .xlsx Export (openpyxl, de/en/es)
- [x] Transport-Modus (See/Luft) + Zonen-Frachtraten
- [x] ZONE_DAI_RATES (Mercosur 0%, USA 10%, Europa/Asien 14%, Sonstige 16%)
- [x] ZONE_FREIGHT_RATES (5 Zonen, See/Luft)
- [x] Grau-CSS fur DB-geladene Felder (.db-loaded, .db-hint)
- [x] DB: 176 -> 226 Produkte (+50: Traktoren, Medizin, Bau, Solar, Chemie, Buro)
- [x] HS-Autocomplete (4+ Ziffern triggert DB-Suggestions)
- [x] DB-Produkt-Expander (Kategorie-Filter + Ubernehmen-Button)
- [x] SEO Meta-Tags + Admin-Dashboard + Dynamische UI
- [x] auto-deploy.sh + systemd Service

## Offen
- [ ] OpenHands Sandbox fixen (Docker-Permission im Container)
- [ ] Ollama Cloud API Key fur KI-Fallback konfigurieren

## URLs
- App: http://localhost:8501 (Host), http://172.18.0.1:8501 (Container)
- OpenHands: http://localhost:3000 (Web-UI, API via /api/v1/app-conversations)
