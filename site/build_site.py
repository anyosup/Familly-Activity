"""data/programs.json 을 웹페이지 1장(docs/index.html)으로 만든다.

실행:  py site/build_site.py
docs/ 폴더는 나중에 GitHub Pages로 그대로 공개된다.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
data = json.loads((ROOT / "data" / "programs.json").read_text(encoding="utf-8"))

# 생태탐방원 → 탐방프로그램 순, 같은 종류 안에서는 유아 가능 → 확인 필요 → 초등 이상 순
order = {"ok": 0, "check": 1, "no": 2}
data["items"].sort(key=lambda i: (i["category"] != "생태탐방원", order[i["age_tag"]], i["park"]))

payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
html = (ROOT / "site" / "template.html").read_text(encoding="utf-8").replace("/*DATA*/", payload)

out = ROOT / "docs" / "index.html"
out.parent.mkdir(exist_ok=True)
out.write_text(html, encoding="utf-8")
print(f"저장: {out}  ({len(data['items'])}건)")
