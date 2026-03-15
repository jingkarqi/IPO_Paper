$ErrorActionPreference = "Stop"

$tectonic = Join-Path $PSScriptRoot "..\\tools\\tectonic\\tectonic.exe"
$xelatex = Get-Command xelatex -ErrorAction SilentlyContinue
$bibtex = Get-Command bibtex -ErrorAction SilentlyContinue

Push-Location $PSScriptRoot

try {
    New-Item -ItemType Directory -Force build | Out-Null

    if (Test-Path $tectonic) {
        & $tectonic -X compile main.tex --outdir build
        Write-Output "Build complete: $PSScriptRoot\\build\\main.pdf"
    }
    elseif ($xelatex -and $bibtex) {
        xelatex -interaction=nonstopmode -halt-on-error main.tex | Out-Null
        bibtex main | Out-Null
        xelatex -interaction=nonstopmode -halt-on-error main.tex | Out-Null
        xelatex -interaction=nonstopmode -halt-on-error main.tex | Out-Null
        Write-Output "Build complete: $PSScriptRoot\\main.pdf"
    }
    else {
        throw "No LaTeX compiler found. Supported options: local tools/tectonic/tectonic.exe or system xelatex + bibtex."
    }
}
finally {
    Pop-Location
}
