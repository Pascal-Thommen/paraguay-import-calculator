# Paraguay Import Calculator — Sprint-Plan 2026-05-21

> **Goal:** 8 Verbesserungen: Bugfix, Admin-Dashboard, SEO, Mobile, dynamische UI, systemd, GitHub-Push

## Status

- [x] 1. Reset-Button löscht Tabelle nicht mehr (BUGFIX — erledigt)
- [ ] 2. Admin/Config-Seite (Modell, Token, Nutzungstracking)
- [ ] 3. SEO-Optimierung (Meta-Tags, SSR, Sitemap)
- [ ] 4. Podman-Deployment bestätigt
- [ ] 5. Mobile-Responsive CSS
- [ ] 6. Dynamische UI: Single/Multi verschmelzen
- [ ] 7. auto-deploy als systemd --user Service
- [ ] 8. Excel-Export (später)

## Architektur-Entscheidung zu Punkt 2

Streamlit hat keine native User-Auth. Für "Einstellungsebene" sehe ich zwei Wege:
  A) Admin-Seite innerhalb der Streamlit-App (versteckt hinter ?admin=true Parameter)
  B) Externes Hermes-Konfigurations-Dashboard

Token-Verbrauch und Modell-Konfiguration sind Hermes-Agent-Features — nicht App-Features.
Nutzer-Tracking (wer hat was berechnet) kann ich mit Streamlit-Session-Logging umsetzen.

=> Klärung nötig: Soll ich A, B, oder beides bauen?
