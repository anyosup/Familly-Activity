"""광주·전남 박물관·미술관·과학관 교육/체험 프로그램을 수집한다.

기관마다 누리집 구조가 달라서 기관별 함수가 하나씩 있다.
한 기관이 실패해도 나머지는 계속 수집한다.
"""
import html
import json
import re

from datetime import datetime, timedelta

from common import KST, age_tag, clean, date_range, fetch, is_group, today

# 지난 프로그램은 몇 페이지 넘기면 나오므로 앞쪽 몇 페이지만 본다
MAX_PAGES = 3


def item(**kw):
    """모든 기관이 같은 모양의 데이터를 내도록 기본값을 채운다."""
    base = {
        "id": "", "source": "", "kind": "", "category": "", "park": "", "title": "", "place": "",
        "target": "", "price": "", "status": "",
        "apply_start": None, "apply_end": None, "event_start": None, "event_end": None,
        "time": "", "summary": "", "url": "",
    }
    base.update(kw)
    base["age_tag"] = age_tag(base["title"], base["target"])
    base["group_only"] = is_group(base["title"], base["target"])
    return base


def still_relevant(it):
    """행사일이나 접수 마감이 오늘 이후인 것만 남긴다."""
    t = today()
    last = max(filter(None, [it["event_end"], it["apply_end"], it["event_start"]]), default=None)
    return last is None or last[:10] >= t


# ── 국립광주박물관 ────────────────────────────────────────────────
def gwangju_museum():
    base = "https://gwangju.museum.go.kr"
    out, seen = [], set()
    for se, cat in (("E_SE01", "유아"), ("E_SE04", "가족"), ("E_SE02", "초등")):
        for page in range(1, MAX_PAGES + 1):
            h = fetch(f"{base}/prog/education/kor/sub03_02/wholeList.do?se={se}&pageIndex={page}")
            cards = re.findall(r'<a href="(/prog/education/kor/sub03_02/view\.do\?[^"]+)" class="link">(.*?)</a>\s*</div>', h, re.S)
            for href, body in cards:
                href = html.unescape(href)
                if href in seen:
                    continue
                seen.add(href)
                fields = {clean(k): clean(v) for k, v in re.findall(r"<li><b>(.*?)</b>(.*?)</li>", body, re.S)}
                title = clean(re.sub(r'<span class="icon2[^>]*>.*?</span>', "", re.search(r'class="tit">(.*?)</strong>', body, re.S).group(1)))
                status = [clean(s) for s in re.findall(r'<span class="stat\d+">(.*?)</span>', body)]
                a1, a2 = date_range(fields.get("접수기간"))
                e1, e2 = date_range(fields.get("교육일시"))
                out.append(item(
                    id="gjm-" + re.sub(r"\D+", "-", href.split("?")[1]).strip("-"),
                    source="국립광주박물관", kind="박물관·미술관", category=f"교육({cat})", park="국립광주박물관",
                    title=title, place="국립광주박물관 (광주 북구 하서로 110)",
                    target=fields.get("대상", ""), price=fields.get("비용", ""),
                    status=status[-1] if status else "", how_to_apply=status[0] if status else "",
                    apply_start=a1, apply_end=a2, event_start=e1, event_end=e2,
                    url=base + href, phone="062-570-7000"))
            if len(cards) < 10:
                break
    return out


# ── 국립나주박물관 ────────────────────────────────────────────────
def naju_museum():
    base = "https://naju.museum.go.kr"
    h = fetch(f"{base}/prog/edu/kor/sub03_02_01/list.do?searchCtgry=&eduRceptMth=")
    out = []
    for block in h.split("fn_view('")[1:]:
        edu_id = block.split("'")[0]
        title = clean(re.search(r'class="tit">(.*?)</strong>', block, re.S).group(1))
        cats = [clean(c) for c in re.findall(r'<span class="cat (?:cat\d+|no-background)">(.*?)</span>', block, re.S)]
        status = re.findall(r'<span class="badge circle stats\d">([^<]+)</span>', block)
        fields = {clean(k): clean(v) for k, v in re.findall(r"<em[^>]*>(.*?)</em><span>(.*?)</span>", block, re.S)}
        a1, a2 = date_range(fields.get("접수기간"))
        e1, e2 = date_range(fields.get("교육기간"))
        out.append(item(
            id="njm-" + edu_id, source="국립나주박물관", kind="박물관·미술관",
            category="교육" + (f"({cats[0]})" if cats else ""), park="국립나주박물관",
            title=title, place="국립나주박물관 (나주 반남면 고분로 747)",
            target=fields.get("교육대상", ""), status=status[-1].strip() if status else "",
            how_to_apply=cats[1] if len(cats) > 1 else "",
            apply_start=a1, apply_end=a2, event_start=e1, event_end=e2,
            url=f"{base}/prog/edu/kor/sub03_02_01/list.do", phone="061-330-7800"))
    return out


# ── 국립광주과학관 ────────────────────────────────────────────────
def science_center():
    base = "https://www.sciencecenter.or.kr"
    out = []
    for path, menu, kind_name in (("edu", "15_2", "교육"), ("ev", "15_1", "행사")):
        for page in range(1, MAX_PAGES + 2):
            h = fetch(f"{base}/kor/{path}/index.do?mode=list&menuId={menu}", {"mode": "list", "page": page})
            blocks = h.split('<div class="desc_thumb"')[1:]
            for b in blocks:
                link = re.search(r'href="(/kor/' + path + r'/index\.do\?mode=view[^"]+)"', b)
                if not link:
                    continue
                href = html.unescape(link.group(1))
                status = clean(re.search(r'<div class="cate[^"]*">(.*?)</div>', b, re.S).group(1))
                spans = [clean(s) for s in re.findall(r'<div class="title">(.*?)</div>', b, re.S)[0].split("</span>")]
                cat = spans[0].strip("[]") if len(spans) > 1 else kind_name
                title = spans[1] if len(spans) > 1 and spans[1] else spans[0]
                fields = {clean(k): clean(v) for k, v in re.findall(r"<b[^>]*>(.*?)</b>\s*<span[^>]*>(.*?)</span>", b, re.S)}
                a1, a2 = date_range(fields.get("접수기간"))
                e1, e2 = date_range(fields.get("교육기간") or fields.get("행사기간") or fields.get("운영기간"))
                out.append(item(
                    id="gsc-" + re.sub(r"\D+", "-", href.split("SEQ=")[-1]),
                    source="국립광주과학관", kind="과학관", category=f"{kind_name}({cat})", park="국립광주과학관",
                    title=title, place="국립광주과학관 (광주 북구 첨단과기로 235)",
                    target=fields.get("모집대상") or fields.get("참가대상", ""),
                    price=fields.get("교육비") or fields.get("참가비", ""), time=fields.get("교육시간", ""),
                    status=status, apply_start=a1, apply_end=a2, event_start=e1, event_end=e2,
                    url=base + href, phone="062-960-6114"))
            if len(blocks) < 6:
                break
    return out


# ── 국립아시아문화전당(ACC) 어린이문화원 ──────────────────────────
def acc_child():
    base = "https://www.acc.go.kr"
    out = []
    for page in (1, 2):
        h = fetch(f"{base}/child/education.do?PID=0302&pageIndex={page}")
        for b in h.split('<a href="?PID=0302&action=Read&bnkey=')[1:]:
            key = b.split("'")[0].split('"')[0]
            ext = re.search(r"fn_linkToReadWithLink\('[^']+','([^']+)'\)", b)
            label = re.search(r'<span class="skedLabel">(.*?)</span>', b, re.S)
            title = clean(re.search(r'<p class="tit">(.*?)</p>', b, re.S).group(1)).replace("\n", " ")
            cont = re.search(r'<p class="cont">(.*?)</p>', b, re.S)
            term = re.search(r'<p class="term">(.*?)</p>', b, re.S)
            price = re.search(r'<p class="price">(.*?)</p>', b, re.S)
            e1, e2 = date_range(clean(term.group(1)) if term else "")
            out.append(item(
                id="acc-" + key, source="ACC 어린이문화원", kind="박물관·미술관", category="어린이 교육",
                park="ACC 어린이문화원", title=title, place="국립아시아문화전당 (광주 동구 문화전당로 38)",
                target=clean(label.group(1)) if label else "",
                price=clean(price.group(1)).replace("가격", "").strip() if price else "",
                summary=clean(cont.group(1)) if cont else "",
                event_start=e1, event_end=e2,
                url=ext.group(1) if ext else f"{base}/child/education.do?PID=0302&action=Read&bnkey={key}",
                phone="1899-5566"))
    return out


# ── 광주시립미술관 (교육·행사 + 문화센터 강좌) ────────────────────
def gwangju_art():
    base = "https://gjartmuse.jeonnam-gwangju.go.kr"
    out = []
    for query, cat in (("pageID=artmuse0417000000&type=edu", "교육·행사"), ("pageID=artmuse0405010000", "문화센터 강좌")):
        for page in range(1, MAX_PAGES + 1):
            h = fetch(f"{base}/pj/pjEducate.php?movePage={page}&action=list&{query}")
            rows = re.findall(r'<li>\s*<a href="(/pj/pjEducate\.php\?[^"]*action=view[^"]*)"\s*>(.*?)</a>\s*</li>', h, re.S)
            for href, b in rows:
                href = html.unescape(href)
                fields = {re.sub(r"[\s·]", "", clean(k)): clean(v) for k, v in re.findall(r"<li><span>(.*?)</span><p>(.*?)</p></li>", b, re.S)}
                title = clean(re.search(r'<span class="title">(.*?)</span>', b, re.S).group(1))
                status = re.search(r'<span class="status[^"]*">(.*?)</span>', b, re.S)
                a1, a2 = date_range(fields.get("접수일자"))
                out.append(item(
                    id="gam-" + re.search(r"seq=(\d+)", href).group(1), source="광주시립미술관", kind="박물관·미술관",
                    category=cat, park="광주시립미술관", title=title,
                    place="광주시립미술관 (광주 북구 하서로 52)", target=fields.get("대상", ""),
                    time=fields.get("시간", ""), how_to_apply=fields.get("접수방법", ""),
                    status=clean(status.group(1)) if status else "",
                    apply_start=a1, apply_end=a2, url=base + href, phone="062-613-7100"))
            if len(rows) < 10:
                break
    return out


# ── 광주시청 바로예약 (역사민속박물관·우치동물원·김치타운 등 시 운영 시설) ──
def gwangju_reserve():
    base = "https://www.gwangju.go.kr/reserve"
    out = []
    for page_id, cate in (("reserve1", "A"), ("reserve2", "B")):
        for page in range(1, 5):
            data = json.loads(fetch(f"{base}/getBookingList.do", {
                "pageId": page_id, "movePage": page, "searchCate1": cate, "searchPeriod": "R",
            }))["dataMap"]
            for v in data["list"]:
                title = clean(v.get("eduNm"))
                place = clean(v.get("eduAddress")) or clean(v.get("areaNm"))
                target = clean(v.get("eduTargetNm"))
                price = v.get("eduPrice")
                a1 = f"{v['startPeriodDate']} {v['startPeriodTime']}" if v.get("startPeriodDate") else None
                a2 = f"{v['endPeriodDate']} {v['endPeriodTime']}" if v.get("endPeriodDate") else None
                out.append(item(
                    id="gjr-" + str(v["bookingCode"]), source="광주시 바로예약", kind="광주시 체험",
                    category=clean(v.get("cateNm")) or ("교육/강좌" if cate == "A" else "견학/체험"),
                    park=place.split()[0] if place else "광주시", title=title, place=place, target=target,
                    price=("무료" if str(price) in ("0", "None", "") else f"{int(price):,}원"),
                    time=f"{v.get('startEduTime') or ''}~{v.get('endEduTime') or ''}".strip("~"),
                    capacity=f"정원 {v.get('limit')}명" if v.get("limit") else "",
                    apply_start=a1, apply_end=a2, event_start=v.get("startEduDate"), event_end=v.get("endEduDate"),
                    url=f"{base}/bookingView.do?pageId={page_id}&searchCate1={cate}&bookingCode={v['bookingCode']}"))
            if page >= int(data.get("pageCnt") or 1):
                break
    return out


# ── 남도향토음식박물관 공지 (체험·교육 모집 글) ─────────────────────
def namdo_food():
    base = "https://gbfmc.or.kr"
    h = fetch(f"{base}/board.es?mid=a40501000000&bid=0022")
    out = []
    for href, title, date in re.findall(r'<a href="(/board\.es\?[^"]*list_no=\d+[^"]*)"[^>]*>(.*?)</a>.*?(\d{4}\.\d{2}\.\d{2})', h, re.S):
        title = clean(title)
        m = re.match(r"\[(\S+?)-(\S+?)\]\s*(.*)", title)
        if not m or m.group(1) not in ("체험", "교육"):
            continue
        if date.replace(".", "-") < (datetime.now(KST) - timedelta(days=60)).strftime("%Y-%m-%d"):
            continue
        kind_, state, name = m.groups()
        out.append(item(
            id="ndf-" + re.search(r"list_no=(\d+)", href).group(1), source="남도향토음식박물관", kind="박물관·미술관",
            category=f"전통음식 {kind_}", park="남도향토음식박물관", title=name,
            place="남도향토음식박물관 (광주 북구 설죽로 477)", status=state,
            target="어린이·가족" if re.search("어린이|가족|아이", name) else ("성인 강좌" if "강좌" in name else ""),
            summary=f"{date.replace('.', '-')} 공지 · 상태: {state}",
            event_start=None, url=base + html.unescape(href), phone="062-410-6847"))
        out[-1]["notice_date"] = date.replace(".", "-")
        out[-1]["closed"] = state == "마감"
    return out


# ── 순천만습지 체험 (탐조산책·조류 탐험·생물 탐험·천문대·계절 특별체험) ──────
def suncheon_bay():
    base = "https://scbay.suncheon.go.kr"
    page = fetch(f"{base}/wetland/booking/0002/")
    programs = re.findall(r'id="tab_(\d+)"[^>]*title="([^"]+)"', page)
    now = datetime.now(KST)
    out = []
    for uid, name in programs:
        data, booked = None, {}
        for m in range(3):  # 이번 달 + 다음 두 달 예약 현황
            y, mo = now.year + (now.month - 1 + m) // 12, (now.month - 1 + m) % 12 + 1
            d = json.loads(fetch(f"{base}/wetland/getYeyakProgramDataAjax.do", {"uid": uid, "calDate": f"{y}{mo:02d}01", "userid": ""}))
            data = data or d.get("programData")
            for r in d.get("progYeyakDataList", []):
                key = (r["yeyakHdate"], r["yeyakTime"])
                booked[key] = booked.get(key, 0) + int(r.get("yeyakPeople") or 0)
        if not data or str(data.get("pause")) == "1":
            continue
        p_end = (data.get("edate") or "")[:10]
        if p_end and p_end < now.strftime("%Y-%m-%d"):
            continue
        p_start = (data.get("sdate") or "")[:10]
        weekdays = {int(x) for x in str(data.get("pmode") or "").split("/") if x.strip().isdigit()}  # 0=일요일
        extra = set(filter(None, str(data.get("adddate") or "").split(",")))
        excluded = set(filter(None, str(data.get("x_date") or "").split(",")))
        sessions = [t for t in str(data.get("ptime") or "").split(",") if t]
        cap = int(data.get("personmax") or 0)
        first = now.date() + timedelta(days=int(data.get("dateterm") or 0))
        last = min(now.date() + timedelta(days=min(int(data.get("datelimit") or 60), 60)),
                   datetime.strptime(p_end, "%Y-%m-%d").date() if p_end else now.date() + timedelta(days=60))
        dates, day = [], max(first, datetime.strptime(p_start, "%Y-%m-%d").date() if p_start else first)
        while day <= last:
            ymd = day.strftime("%Y%m%d")
            if ((day.isoweekday() % 7) in weekdays or ymd in extra) and ymd not in excluded:
                left = sum(max(cap - booked.get((ymd, t), 0), 0) for t in sessions)
                dates.append({"date": day.isoformat(), "left": left, "open": left > 0})
            day += timedelta(days=1)
        content = clean(data.get("content"))
        age = re.search(r"\d+\s*살\s*\(만\s*\d+\s*세\)\s*이상[^\n]*|만\s*\d+\s*세\s*이상[^\n]*", content)
        fee = re.search(r"참가비\s*[:：]?\s*([^\n]+)", content)
        out.append(item(
            id=f"scb-{uid}", source="순천만습지", kind="순천만습지", category="생태체험", park="순천만습지",
            title=name if name in data.get("subject", name) else data.get("subject", name),
            place=clean(data.get("area")) or "순천만습지 (순천시 순천만길 513-25)",
            target=age.group(0).strip() if age else "", price=fee.group(1).strip() if fee else "",
            time=", ".join(sessions), capacity=f"회당 {cap}명" if cap else "",
            event_start=p_start or None, event_end=p_end or None,
            summary=content[:1200], url=f"{base}/wetland/booking/0002/#{uid}",
            phone=data.get("departtel") or "061-749-6072"))
        out[-1]["dates"] = dates
    return out


# 함수 → 데이터에 찍히는 출처 이름 (수집 실패 시 이전 데이터를 유지하는 데 쓴다)
SOURCES = {
    gwangju_museum: "국립광주박물관",
    naju_museum: "국립나주박물관",
    science_center: "국립광주과학관",
    acc_child: "ACC 어린이문화원",
    gwangju_art: "광주시립미술관",
    gwangju_reserve: "광주시 바로예약",
    namdo_food: "남도향토음식박물관",
    suncheon_bay: "순천만습지",
}
FAILED = set()  # 이번 실행에서 실패한 출처 이름


def collect():
    items = []
    for src, label in SOURCES.items():
        try:
            raw = src()
            if not raw:  # 지난 글까지 0건이면 접속이 막혔거나 화면 구조가 바뀐 것
                raise RuntimeError("목록이 비어 있음")
            got = [i for i in raw if still_relevant(i)]
            items += got
            print(f"▶ {label}: {len(got)}건")
            for i in got:
                flag = " [단체]" if i["group_only"] else ""
                print(f"    - {i['title'][:40]}{flag}  접수 {i['apply_start'] or '-'}~{i['apply_end'] or '-'}  대상 {i['target'][:20]}")
        except Exception as e:  # 한 기관이 고장 나도 나머지는 계속
            FAILED.add(label)
            print(f"▶ {label}: 실패 ({e!r})")
    return items
