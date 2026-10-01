# 🌳 우리 가족 체험 달력

광주·전남(+전북 생태탐방원) 국립공원 탐방프로그램과 생태탐방원 프로그램을 한 페이지에 모아 보는 가족용 웹페이지.

## 구성

| 파일 | 하는 일 |
|---|---|
| `collector/collect_knps.py` | 국립공원 예약시스템에서 프로그램을 모아 `data/programs.json`에 저장 |
| `site/template.html` | 웹페이지 디자인·기능 |
| `site/build_site.py` | 데이터를 넣어 `docs/index.html` 생성 |
| `.github/workflows/update.yml` | 매일 06시(한국시간) 자동 실행 |

## 내 컴퓨터에서 실행

```
py collector/collect_knps.py
py site/build_site.py
```

## 수집 대상 바꾸기

`collector/collect_knps.py` 위쪽의 `TRAIL_PARKS`, `ECO_CENTERS`를 고친다.
