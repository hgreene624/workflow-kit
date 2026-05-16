# pdf-cuartilla — HTML → PDF via headless Edge
# Usage:
#   .\build.ps1 -Html "C:\path\to\file.html" -Pdf "C:\path\to\file.pdf"
param(
  [Parameter(Mandatory=$true)][string]$Html,
  [Parameter(Mandatory=$true)][string]$Pdf
)

$edge = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if (-not (Test-Path $edge)) {
  $alt = "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe"
  if (Test-Path $alt) { $edge = $alt } else { throw "Edge not found at known paths." }
}
if (-not (Test-Path $Html)) { throw "HTML source not found: $Html" }

$url = "file:///$($Html -replace '\\','/')"
& $edge --headless --disable-gpu --no-pdf-header-footer --print-to-pdf="$Pdf" $url 2>&1 | Out-Null

if (Test-Path $Pdf) {
  "OK -> $Pdf ($((Get-Item $Pdf).Length) bytes)"
} else {
  throw "PDF generation failed."
}
