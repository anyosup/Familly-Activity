"""광주·전남 박물관·미술관·과학관 교육/체험 프로그램을 수집한다.

기관마다 누리집 구조가 달라서 기관별 함수가 하나씩 있다.
한 기관이 실패해도 나머지는 계속 수집한다.
"""
import html
import re

from common import age_tag, clean, date_range, fetch, is_group, today

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


SOURCES = [gwangju_museum, naju_museum, science_center, acc_child, gwangju_art]


def collect():
    items = []
    for src in SOURCES:
        try:
            got = [i for i in src() if still_relevant(i)]
            items += got
            print(f"▶ {src.__name__}: {len(got)}건")
            for i in got:
                flag = " [단체]" if i["group_only"] else ""
                print(f"    - {i['title'][:40]}{flag}  접수 {i['apply_start'] or '-'}~{i['apply_end'] or '-'}  대상 {i['target'][:20]}")
        except Exception as e:  # 한 기관이 고장 나도 나머지는 계속
            print(f"▶ {src.__name__}: 실패 ({e!r})")
    return items
