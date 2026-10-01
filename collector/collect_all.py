"""모든 출처를 수집해 data/programs.json 하나로 합친다.

실행:  py collector/collect_all.py

어떤 출처가 실패하면(해외 접속 차단, 사이트 점검 등) 그 출처는 지난번 데이터를 그대로 유지하고
'as_of'(언제 기준 정보인지)를 남긴다. 그래서 GitHub(해외 서버)와 집 PC(국내) 어디서 돌려도 데이터가 줄지 않는다.
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import collect_culture  # noqa: E402
import collect_festival  # noqa: E402
import collect_knps  # noqa: E402
from common import KST  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "data" / "programs.json"
KNPS_SOURCES = {"국립공원 탐방프로그램", "국립공원 생태탐방원", "국립공원 생태탐방원 숙박", "국립공원 생태탐방원 기획"}
FESTIVAL_SOURCES = {"한국관광공사"}


def main():
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M")
    old = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {"items": []}

    items, failed = [], set()
    for mod, labels in ((collect_knps, KNPS_SOURCES), (collect_culture, set()), (collect_festival, FESTIVAL_SOURCES)):
        try:
            got = mod.collect()
            items += got
            if mod is collect_knps and not got:
                failed |= labels
        except Exception as e:
            print(f"!! {mod.__name__} 실패: {e!r}")
            failed |= labels
    failed |= collect_culture.FAILED
    if not os.environ.get("TOURAPI_KEY"):  # 키 없는 곳(집 PC)에서 돌리면 축제는 지난 데이터 유지
        failed |= FESTIVAL_SOURCES

    for i in items:
        if not i.get("kind"):  # 국립공원 수집기는 kind 를 따로 안 넣으므로 여기서 채운다
            i["kind"] = "생태탐방원" if i["category"] == "생태탐방원" else "국립공원"
        i.setdefault("group_only", False)
        i["as_of"] = now

    # 실패한 출처는 지난 데이터 중 아직 유효한 것을 이어 붙인다
    kept = 0
    for i in old["items"]:
        if i.get("source") in failed and collect_culture.still_relevant({k: i.get(k) for k in ("event_end", "apply_end", "event_start")}):
            i.setdefault("as_of", old.get("updated_at", ""))
            items.append(i)
            kept += 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"updated_at": now, "items": items}, ensure_ascii=False, indent=2), encoding="utf-8")

    kinds = {}
    for i in items:
        kinds[i["kind"]] = kinds.get(i["kind"], 0) + 1
    print(f"\n완료: 총 {len(items)}건 {kinds}")
    if failed:
        print(f"이전 데이터 유지: {sorted(failed)} → {kept}건")


if __name__ == "__main__":
    main()
