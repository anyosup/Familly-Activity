"""한국관광공사 TourAPI로 광주·전남 축제를 수집한다.

공공데이터포털(data.go.kr)에서 '한국관광공사_국문 관광정보 서비스_GW' 활용신청 후 받은
인증키(Decoding 키)를 환경변수 TOURAPI_KEY 에 넣어야 동작한다. 키가 없으면 건너뛴다.
"""
import json
import os
import urllib.parse

from common import age_tag, fetch, today

API = "https://apis.data.go.kr/B551011/KorService2/searchFestival2"
REGION_WORDS = ["광주", "전남", "전라남도"]  # 주소에 이 글자가 있으면 포함
DAYS_AHEAD = 90


def fmt(d):
    return f"{d[:4]}-{d[4:6]}-{d[6:8]}" if d and len(d) >= 8 else None


def collect():
    key = os.environ.get("TOURAPI_KEY", "").strip()
    if not key:
        print("▶ 축제(TourAPI): 인증키가 없어 건너뜀")
        return []
    start = today().replace("-", "")
    out, page = [], 1
    while True:
        q = urllib.parse.urlencode({
            "serviceKey": key, "MobileOS": "ETC", "MobileApp": "family-activity", "_type": "json",
            "eventStartDate": start, "numOfRows": 200, "pageNo": page, "arrange": "A",
        })
        body = json.loads(fetch(f"{API}?{q}"))["response"]["body"]
        rows = (body.get("items") or {}).get("item") or []
        for r in rows:
            addr = f"{r.get('addr1', '')} {r.get('addr2', '')}".strip()
            if not any(w in addr for w in REGION_WORDS):
                continue
            title = r.get("title", "")
            out.append({
                "id": "fes-" + r["contentid"], "source": "한국관광공사", "kind": "축제", "category": "축제·행사",
                "park": addr.split()[1] if len(addr.split()) > 1 else addr, "title": title, "place": addr,
                "target": "", "price": "", "status": "",
                "apply_start": None, "apply_end": None,
                "event_start": fmt(r.get("eventstartdate")), "event_end": fmt(r.get("eventenddate")),
                "summary": "", "phone": r.get("tel", ""),
                "image": r.get("firstimage", ""),
                "url": "https://korean.visitkorea.or.kr/detail/fes_detail.do?cotid=" + r.get("contentid", ""),
                "age_tag": age_tag(title, ""), "group_only": False,
            })
        if page * 200 >= int(body.get("totalCount", 0)):
            break
        page += 1
    print(f"▶ 축제(TourAPI): {len(out)}건")
    return out
