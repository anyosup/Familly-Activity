"""국립공원 예약시스템에서 광주·전남권 탐방프로그램 + 생태탐방원 프로그램을 수집한다."""
import html
import json
import re
from datetime import datetime, timedelta

import common
from common import KST, age_tag, clean

BASE = "https://reservation.knps.or.kr"

# ── 설정: 여기만 고치면 수집 대상이 바뀐다 ──────────────────────────
# 탐방프로그램: 공원코드(목록 조회용) → 포함할 세부 사무소 코드와 지역
TRAIL_PARKS = {
    "B17": {"무등산": "B171", "무등산동부": "B172"},
    "B20": {"월출산": "B201"},
    "B01": {"지리산전남": "B013"},
    "B04": {"내장산백암": "B041"},
    "B09": {"다도해해상": "B091", "다도해해상서부": "B092"},
}
# 생태탐방원: 예약코드 → 이름
ECO_CENTERS = {
    "B231002": "무등산생태탐방원",
    "B014003": "지리산생태탐방원",
    "B331001": "내장산생태탐방원",
    "B183001": "변산반도생태탐방원",
}
ECO_DAYS_AHEAD = 60  # 생태탐방원은 오늘부터 며칠 뒤까지 조회할지
# ──────────────────────────────────────────────────────────────────

HEADERS = {"Referer": BASE + "/trprogram/searchTrailProgram.do", "X-Requested-With": "XMLHttpRequest"}


def fetch(url, data=None):
    return common.fetch(url, data, HEADERS)


# ── 탐방프로그램 ──────────────────────────────────────────────────
ROW_RE = re.compile(r"<tr>(.*?)</tr>", re.S)
TD_RE = re.compile(r"<td[^>]*>(.*?)</td>", re.S)
LINK_RE = re.compile(r'href="(/contents/G/serviceGuide\.do\?parkId=(\w+)&(?:amp;)?prdId=(\w+)&(?:amp;)?orgnztGbn=(\w+))"')
DL_RE = re.compile(r"<dt>\s*(.*?)\s*</dt>\s*<dd>(.*?)</dd>", re.S)


def collect_trail():
    items = []
    for park_code, units in TRAIL_PARKS.items():
        wanted = set(units.values())
        for gbn, gbn_name in (("G", "해설·생태관광·환경교육"), ("H", "치유·특화")):
            page = fetch(BASE + "/trprogram/trprogramList.do", {
                "dept_id": park_code, "orgnzt_gbn": gbn, "pageNo": 1, "listScale": 100,
            })
            for row in ROW_RE.findall(page):
                link = LINK_RE.search(row)
                tds = [clean(t) for t in TD_RE.findall(row)]
                if not link or len(tds) < 5:
                    continue
                path, park_id, prd_id, _ = link.groups()
                if park_id not in wanted:
                    continue
                unit_name = next(k for k, v in units.items() if v == park_id)
                period = re.findall(r"\d{4}-\d{2}-\d{2}", tds[4])
                detail_url = BASE + html.unescape(path)
                detail = dict((clean(k), clean(v)) for k, v in DL_RE.findall(fetch(detail_url)))
                title = tds[3]
                target = detail.get("참가대상", "")
                items.append({
                    "id": prd_id,
                    "source": "국립공원 탐방프로그램",
                    "category": gbn_name,
                    "park": unit_name,
                    "title": title,
                    "place": detail.get("집결장소") or tds[2],
                    "period_start": period[0] if period else None,
                    "period_end": period[1] if len(period) > 1 else None,
                    "target": target,
                    "age_tag": age_tag(title, target),
                    "duration": detail.get("소요시간", ""),
                    "capacity": detail.get("참가인원", ""),
                    "how_to_apply": detail.get("참가방법", ""),
                    "phone": detail.get("문의전화", ""),
                    "summary": detail.get("주요내용", ""),
                    "notes": detail.get("주의사항", ""),
                    "url": detail_url,
                })
                print(f"  [{unit_name}] {title}  → 대상: {target or '-'}")
    return items


# ── 생태탐방원 ────────────────────────────────────────────────────
TIME_LABEL = {"0600401": "오전 10:00~12:00", "0600402": "오후 14:00~16:00", "0600403": "종일형", "0600404": "당일형"}


def collect_eco():
    items = []
    today = datetime.now(KST).date()
    for dept_id, center in ECO_CENTERS.items():
        programs = {}
        # 1주 단위로 끊어서 조회
        for start in range(0, ECO_DAYS_AHEAD, 7):
            d1 = today + timedelta(days=start)
            d2 = min(d1 + timedelta(days=6), today + timedelta(days=ECO_DAYS_AHEAD))
            raw = fetch(BASE + "/eco/getEcoProgramInfo.do", {
                "deptId": dept_id, "useBgnDt": d1.strftime("%Y%m%d"),
                "useEndDt": d2.strftime("%Y%m%d"), "hrkPrdCtgId": "06004",
            })
            info = json.loads(raw).get("insttGoodsInfo", [])
            # 같은 상품·날짜가 [청소년, 성인] 두 줄로 온다
            for youth, adult in zip(info[0::2], info[1::2]):
                p = programs.setdefault(youth["prdId"], {
                    "title": youth["prdNm"],
                    "time": TIME_LABEL.get(youth["prdCtgId"], ""),
                    "price_youth": youth["salAmt"],
                    "price_adult": adult["salAmt"],
                    "dates": {},
                })
                left = youth["maxNopCnt"] - (youth["rsrvtCnt"] + adult["rsrvtCnt"])
                open_ = youth["rsvtPsblYn"] == "Y" and youth["prdSalStcd"] == "N"
                if youth["maxNopCnt"] >= 99999:
                    left = None  # 인원 제한 없음
                p["dates"][youth["useDt"]] = {"left": left, "open": open_}
        for prd_id, p in programs.items():
            dates = [{"date": d, **v} for d, v in sorted(p["dates"].items())]
            items.append({
                "id": prd_id,
                "source": "국립공원 생태탐방원",
                "category": "생태탐방원",
                "park": center,
                "title": p["title"],
                "place": center,
                "time": p["time"],
                "price": f"청소년 {p['price_youth']:,}원 / 성인 {p['price_adult']:,}원",
                "target": "",
                "age_tag": age_tag(p["title"], ""),
                "dates": dates,
                "how_to_apply": "생태탐방원 예약 (2인 이상)",
                "url": f"{BASE}/eco/searchEcoReservation.do?deptId={dept_id}",
            })
            n_open = sum(1 for d in dates if d["open"] and (d["left"] is None or d["left"] > 0))
            print(f"  [{center}] {p['title']}  → 예약가능 {n_open}일 / 조회 {len(dates)}일")
    return items


def collect():
    print("▶ 국립공원 탐방프로그램")
    trail = collect_trail()
    print("▶ 국립공원 생태탐방원")
    return trail + collect_eco()
