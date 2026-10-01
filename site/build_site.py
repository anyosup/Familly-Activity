"""data/programs.json 으로 웹페이지(docs/index.html)와 구독용 달력(docs/calendar.ics)을 만든다.

실행:  py site/build_site.py
docs/ 폴더는 GitHub Pages로 그대로 공개된다.
"""
import json
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
data = json.loads((ROOT / "data" / "programs.json").read_text(encoding="utf-8"))

# ── 관심 목록(🔥): 키워드가 맞고, 초등 이상·단체 전용이 아니면 표시 ─────────
watch = json.loads((ROOT / "data" / "watchlist.json").read_text(encoding="utf-8"))
for it in data["items"]:
    text = " ".join(str(it.get(k) or "") for k in ("title", "category", "park", "source", "place"))
    hit = next((w["name"] for w in watch["watch"] if any(k in text for k in w["keywords"])), None)
    it["hot"] = hit if hit and it.get("age_tag") != "no" and not it.get("group_only") else None
data["links"] = watch.get("links", [])

# ── 웹페이지 ──────────────────────────────────────────────────────
payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
html = (ROOT / "site" / "template.html").read_text(encoding="utf-8").replace("/*DATA*/", payload)
DOCS.mkdir(exist_ok=True)
(DOCS / "index.html").write_text(html, encoding="utf-8")


# ── 구독용 달력: 신청 오픈 일정 ─────────────────────────────────────
# 단체 전용·초등 이상은 빼고, 오늘 이후 신청이 열리는 것만 넣는다.
def esc(s):
    return str(s or "").replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")


def fold(line):
    """달력 파일은 한 줄 75바이트 제한이 있어서 길면 접는다."""
    out, cur = [], b""
    for ch in line:
        b = ch.encode("utf-8")
        if len(cur) + len(b) > 73:
            out.append(cur.decode("utf-8"))
            cur = b" " + b
        else:
            cur += b
    out.append(cur.decode("utf-8"))
    return "\r\n".join(out)


today = data["updated_at"][:10]
events = []
for it in data["items"]:
    start = it.get("apply_start")
    if not start or start[:10] < today or it.get("group_only") or it.get("age_tag") == "no":
        continue
    day = start[:10].replace("-", "")
    hot = "🔥 " if it.get("hot") else ""
    if len(start) > 10:  # 시각이 있으면 그 시각에 30분짜리 일정 + 30분 전 알림
        hhmm = start[11:16].replace(":", "")
        end = (datetime.strptime(start, "%Y-%m-%d %H:%M") + timedelta(minutes=30)).strftime("%Y%m%dT%H%M00")
        when = [f"DTSTART;TZID=Asia/Seoul:{day}T{hhmm}00", f"DTEND;TZID=Asia/Seoul:{end}"]
        alarm = "-PT30M"
    else:  # 날짜만 있으면 종일 일정 + 전날 알림
        nxt = (datetime.strptime(day, "%Y%m%d") + timedelta(days=1)).strftime("%Y%m%d")
        when = [f"DTSTART;VALUE=DATE:{day}", f"DTEND;VALUE=DATE:{nxt}"]
        alarm = "-PT15H"  # 전날 오전 9시쯤
    desc = f"{it.get('park', '')}\\n대상: {esc(it.get('target'))}\\n접수: {it.get('apply_start')} ~ {it.get('apply_end') or ''}\\n{it['url']}"
    events += [
        "BEGIN:VEVENT", f"UID:{it['id']}-apply@family-activity", f"DTSTAMP:{day}T000000Z", *when,
        f"SUMMARY:{hot or '🔔 '}신청 오픈: {esc(it['title'])}", f"LOCATION:{esc(it.get('place'))}",
        f"DESCRIPTION:{desc}", f"URL:{it['url']}",
        "BEGIN:VALARM", f"TRIGGER:{alarm}", "ACTION:DISPLAY", f"DESCRIPTION:곧 신청 오픈: {esc(it['title'])}", "END:VALARM",
        # 관심 체험은 하루 전에도 한 번 더 알림 (종일 일정이면 전날 밤 9시)
        *(["BEGIN:VALARM", "TRIGGER:-PT27H" if len(start) <= 10 else "TRIGGER:-PT24H", "ACTION:DISPLAY",
           f"DESCRIPTION:🔥 내일 신청 오픈: {esc(it['title'])}", "END:VALARM"] if hot else []),
        "END:VEVENT",
    ]

cal = [
    "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//family-activity//KO", "CALSCALE:GREGORIAN",
    "X-WR-CALNAME:우리 가족 체험 - 신청 오픈", "X-WR-TIMEZONE:Asia/Seoul",
    "REFRESH-INTERVAL;VALUE=DURATION:PT12H", "X-PUBLISHED-TTL:PT12H",
    "BEGIN:VTIMEZONE", "TZID:Asia/Seoul", "BEGIN:STANDARD", "DTSTART:19700101T000000",
    "TZOFFSETFROM:+0900", "TZOFFSETTO:+0900", "TZNAME:KST", "END:STANDARD", "END:VTIMEZONE",
    *events, "END:VCALENDAR",
]
(DOCS / "calendar.ics").write_text("\r\n".join(fold(line) for line in cal) + "\r\n", encoding="utf-8", newline="")

print(f"저장: docs/index.html ({len(data['items'])}건), docs/calendar.ics (신청 오픈 {events.count('BEGIN:VEVENT')}건)")
