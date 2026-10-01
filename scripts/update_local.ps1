# 집 PC에서 매일 실행: 국내에서만 열리는 사이트(국립광주과학관·국립광주박물관 등)까지 수집해 GitHub에 올린다.
# Windows 작업 스케줄러가 이 파일을 실행한다. 직접 실행해도 된다:
#   powershell -ExecutionPolicy Bypass -File scripts\update_local.ps1
# 실행 기록은 logs\update_local.log 에 남는다.

$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$env:PYTHONIOENCODING = 'utf-8'

New-Item -ItemType Directory -Force (Join-Path $root 'logs') | Out-Null
$log = Join-Path $root 'logs\update_local.log'

function Log($msg) {
    $line = "[{0}] {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $msg
    Add-Content -Path $log -Value $line -Encoding utf8
}

function Run($label, [scriptblock]$cmd) {
    $out = & $cmd 2>&1 | Out-String
    Add-Content -Path $log -Value $out -Encoding utf8
    if ($LASTEXITCODE -ne 0) { Log "실패: $label (코드 $LASTEXITCODE)"; return $false }
    return $true
}

Log '시작'
# GitHub 자동 실행이 올린 최신 데이터(축제 등)를 먼저 받는다
if (-not (Run 'git pull' { git pull --rebase --autostash origin main })) { Log '중단'; exit 1 }
if (-not (Run '수집' { py collector/collect_all.py })) { Log '중단'; exit 1 }
if (-not (Run '웹페이지 만들기' { py site/build_site.py })) { Log '중단'; exit 1 }

git add data docs
git diff --cached --quiet
if ($LASTEXITCODE -eq 0) { Log '바뀐 내용 없음'; exit 0 }

$stamp = Get-Date -Format 'yyyy-MM-dd HH:mm'
Run 'commit' { git commit -m "데이터 갱신 (집 PC) $stamp" } | Out-Null
# 그 사이 GitHub 쪽에서 올라온 게 있으면 합치되, 데이터 파일은 방금 만든 것을 우선한다
for ($i = 0; $i -lt 3; $i++) {
    if (Run 'push' { git push origin main }) { Log '완료'; exit 0 }
    Run 'pull 재시도' { git pull --rebase -X theirs origin main } | Out-Null
}
Log '중단: push 실패'
exit 1
