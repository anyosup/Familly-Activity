"""수집기들이 같이 쓰는 기능: 웹페이지 가져오기, 글자 정리, 날짜 읽기, 연령·단체 표시."""
import html
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))
UA = "Mozilla/5.0 (family-kids-activity-calendar; personal use)"


def today():
    return datetime.now(KST).strftime("%Y-%m-%d")


def fetch(url, data=None, headers=None, encoding="utf-8"):
    body = urllib.parse.urlencode(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        text = r.read().decode(encoding, errors="replace")
    time.sleep(0.5)  # 사이트에 부담 주지 않도록 천천히
    return text


def clean(s):
    s = re.sub(r"<br\s*/?>", "\n", s or "")
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s).replace("\xa0", " ")
    s = re.sub(r"[ \t]+", " ", s)
    return re.sub(r"\n\s*\n+", "\n", s).strip()


# ── 날짜 ────────────────────────────────────────────────────────────
_DATE = r"(\d{4})\s*[-./년]\s*(\d{1,2})\s*[-./월]\s*(\d{1,2})\s*일?\.?(?:\s*\([^)]*\))?(?:\s+(\d{1,2}):(\d{2}))?"


def parse_dates(text):
    """'2026-02-24 17:00 ~ 2026-10-05 17:00', '2026년 11월 02일 ~ 2026년 11월 27일' 등에서 날짜를 뽑는다."""
    out = []
    for y, m, d, hh, mm in re.findall(_DATE, text or ""):
        s = f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
        out.append(f"{s} {int(hh):02d}:{mm}" if hh else s)
    return out


def date_range(text):
    ds = parse_dates(text)
    if not ds:
        return None, None
    return ds[0], ds[1] if len(ds) > 1 else ds[0]


# ── 연령·단체 표시: 거르지 않고 표시만 붙인다 ─────────────────────────
KID_OK = ["유아", "영유아", "어린이", "아동", "가족", "모든 연령", "전연령", "전 연령", "모든연령",
          "구분 없음", "구분없음", "누구나", "제한없음", "제한 없음", "미취학", "보호자 동반"]
KID_NO = ["성인 강좌", "초등학생 이상", "초등 이상", "초등", "중학생", "중등", "고등학생", "청소년", "성인", "일반",
          "노인", "어르신", "외국인", "이주노동자", "직업탐험", "영재"]
CHILD_AGE = 5  # 우리 아이 나이(만 나이 아님, 대략). 범위 판단에만 쓴다


def age_tag(title, target):
    text = f"{title} {target}"
    # '초등학생 이상 누구나' 처럼 하한이 분명하면 '누구나'보다 우선한다
    if re.search(r"(초등학생|초등|초\s*\d|중학생|중등|고등학생|성인)\s*(학생)?\s*이상", text):
        return "no"
    m = re.search(r"(\d+)\s*세?\s*[~\-]\s*(\d+)\s*세", text)  # 6~10세
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        return "ok" if lo <= CHILD_AGE <= hi else ("check" if lo <= CHILD_AGE + 2 else "no")
    m = re.search(r"(\d+)\s*세\s*이상", text)
    if m:
        return "ok" if int(m.group(1)) <= CHILD_AGE else ("check" if int(m.group(1)) <= CHILD_AGE + 2 else "no")
    if any(k in text for k in KID_OK):
        return "ok"
    if any(k in text for k in KID_NO):
        return "no"
    return "check"


GROUP_WORDS = ["단체", "학급"]


def is_group(title, target=""):
    """학교·유치원 단체 전용이면 True (가족은 신청 불가)"""
    if "단체" in title and "개인" not in title:
        return True
    text = f"{title} {target}"
    return any(w in text for w in GROUP_WORDS) and "가족" not in text and "개인" not in text
