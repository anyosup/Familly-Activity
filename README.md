# 🌳 우리 가족 체험 달력

광주·전남 국립공원·생태탐방원·박물관·미술관·과학관·축제의 체험 프로그램을 한 페이지에 모아 보는 가족용 웹페이지.

## 구성

| 파일 | 하는 일 |
|---|---|
| `collector/collect_all.py` | 아래 수집기를 모두 돌려 `data/programs.json` 하나로 저장 |
| `collector/collect_knps.py` | 국립공원 탐방프로그램·생태탐방원 |
| `collector/collect_culture.py` | 국립광주·나주박물관, 국립광주과학관, ACC 어린이문화원, 광주시립미술관 |
| `collector/collect_festival.py` | 광주·전남 축제 (TourAPI 인증키 필요) |
| `site/template.html` | 웹페이지 디자인·기능 |
| `site/build_site.py` | `docs/index.html` 과 신청 오픈 구독 달력 `docs/calendar.ics` 생성 |
| `.github/workflows/update.yml` | 매일 06시(한국시간) 자동 실행 |

## 내 컴퓨터에서 실행

```
py collector/collect_all.py
py site/build_site.py
```

## 수집 대상 바꾸기

국립공원은 `collector/collect_knps.py` 위쪽의 `TRAIL_PARKS`, `ECO_CENTERS`, 박물관 등은 `collector/collect_culture.py` 의 `SOURCES` 를 고친다.
