import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
CDN = '<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>'

t = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
s = json.load(open(os.path.join(ROOT, "data", "summary.json")))
g = open(os.path.join(ROOT, "data", "zips.json"), encoding="utf-8").read()
body = (t.replace("__DATA__", g).replace("__SUMMARY__", json.dumps(s))
         .replace("__N_RENT__", f"{s['n_rentals']:,}")
         .replace("__WAGE__", f"{s['region_wage']:.2f}")
         .replace("__RENT_MED__", f"{s['zip_rent_median']:,.0f}")
         .replace("__ACC_MED__", str(int(s["zip_access_median"]))))

open(os.path.join(HERE, "rent-vs-reach.artifact.html"), "w", encoding="utf-8").write(body)

standalone = ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
              "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
              "<style>body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n"
              "</head>\n<body>\n"
              + body.replace(CDN, '<script src="d3.min.js"></script>')
              + "\n</body>\n</html>\n")
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(standalone)
print("wrote index.html and scripts/rent-vs-reach.artifact.html")
