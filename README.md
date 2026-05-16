# sommersause-festival.github.io

## Run locally

This project is a static website (`index.html` + `assets/`) with a build step for FAQ data.
The FAQ is generated from `FAQ_Sause_eV_Website_Pflege.xlsx` into `assets/data/faq.json`.

```bash
cd /Users/gabrieladams/Documents/Sause/Website/sommersause-festival
python3 scripts/build_faq_json.py
python3 -m http.server 8000
```

Then open:

```text
http://localhost:8000
```

Stop the server with `Ctrl + C`.

## FAQ data pipeline

If you update the Excel file, regenerate JSON before local testing or deployment:

```bash
python3 scripts/build_faq_json.py
```
