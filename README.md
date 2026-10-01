# 🌳 우리 가족 체험 달력

광주·전남 국립공원·생태탐방원·박물관·미술관·과학관·축제의 체험 프로그램을 한 페이지에 모아 보는 가족용 웹페이지.

## 구성

| 파일 | 하는 일 |
|---|---|
| `collector/collect_all.py` | 아래 수집기를 모두 돌려 `data/programs.json` 하나로 저장 |
| `collector/collect_knps.py` | 국립공원 탐방프로그램, 생태탐방원 프로그램·기획프로그램(계절 특집)·숙박 |
| `collector/collect_culture.py` | 국립광주·나주박물관, 국립광주과학관, ACC 어린이문화원, 광주시립미술관, 광주시청 바로예약(역사민속박물관·우치동물원 등), 남도향토음식박물관 |
| `data/watchlist.json` | 🔥 관심 목록 (키워드·바로가기). 고치면 다음 갱신부터 반영 |
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

## 집 PC 매일 실행 (국내에서만 열리는 사이트용)

국립광주과학관·국립광주박물관은 해외(GitHub 서버) 접속을 막아서, 집 PC에서도 매일 한 번 수집해 올린다.

- 실행 파일: `scripts/update_local.ps1` (Windows 작업 스케줄러 "가족체험달력 갱신"이 매일 08:00 실행, PC가 꺼져 있었으면 켜진 뒤 실행)
- 기록: `logs/update_local.log`
- 수집에 실패한 출처는 이전 데이터를 유지하므로 GitHub 실행과 PC 실행이 섞여도 데이터가 줄지 않는다.
