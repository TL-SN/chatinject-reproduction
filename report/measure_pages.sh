#!/usr/bin/env bash
# 重建 dry-run 并用 Word COM 测页数 + 输出标题-页码分布
set -e
cd "$(dirname "$0")"
PY=/home/tlsn/.venvs/chatinject/bin/python
$PY write_report.py --dry-run > /dev/null
cp /tmp/report_dry_run.docx _pagecheck.docx
powershell.exe -NoProfile -Command "
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
\$w = New-Object -ComObject Word.Application; \$w.Visible = \$false
\$d = \$w.Documents.Open('E:\tlsn\chatInject_reproduction\report\_pagecheck.docx')
Write-Output ('PAGES=' + \$d.ComputeStatistics(2))
foreach (\$p in \$d.Paragraphs) {
  \$t = \$p.Range.Text.Trim()
  if (\$t.Length -gt 1 -and \$t.Length -lt 30 -and \$p.Style.NameLocal -match '标题') {
    Write-Output ('  p' + \$p.Range.Information(3) + '  ' + \$t)
  }
}
\$d.Close(0); \$w.Quit()
" 2>/dev/null
