"""모든 출처를 수집해 data/programs.json 하나로 합친다.

실행:  py collector/collect_all.py
"""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import collect_culture  # noqa: E402
import collect_festival  # noqa: E402
import collect_knps  # noqa: E402
from common import KST  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "data" / "programs.json"


def main():
    items = []
    for mod in (collect_knps, collect_culture, collect_festival):
        try:
            items += mod.collect()
        except Exception as e:  # 한 출처가 고장 나도 나머지는 저장
            print(f"!! {mod.__name__} 실패: {e!r}")

    for i in items:  # 국립공원 수집기는 kind 를 따로 안 넣으므로 여기서 채운다
        if not i.get("kind"):
            i["kind"] = "생태탐방원" if i["category"] == "생태탐방원" else "국립공원"
        i.setdefault("group_only", False)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "updated_at": datetime.now(KST).strftime("%Y-%m-%d %H:%M"),
        "items": items,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    kinds = {}
    for i in items:
        kinds[i["kind"]] = kinds.get(i["kind"], 0) + 1
    print(f"\n완료: 총 {len(items)}건 {kinds}")


if __name__ == "__main__":
    main()
