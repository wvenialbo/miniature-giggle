##
## Run the CI/CD toolchain
##

$venv = '.venv'

$project = $args[0]

if (-not $project) {
    $project = './src/goesdl'
}

$isFolder = Test-Path -Type Container -LiteralPath $project

# Run the document linters

Write-Host "Running CI/CD toolchain for $project"
Write-Host ""

# Activate the environment if it is not active

$isVirtualEnvActive = $true

if (-not $env:VIRTUAL_ENV) {
    $isVirtualEnvActive = $false
    & $venv/Scripts/Activate.ps1
}

Write-Host "--- Running ruff {check|format} <file> [--fix]"
ruff check $project
# ruff check --fix $project
# ruff format $project

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
Write-Host ""

Write-Host "--- Running ty check <file>"
ty check $project

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
Write-Host ""

Write-Host "--- Running mypy {<file>|<dir>}"
mypy $project

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
Write-Host ""

Write-Host "--- Running pyright {<file>|<dir>}"
pyright $project

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
Write-Host ""

Write-Host "--- Running pydoclint {<file>|<dir>} [--quiet]"
pydoclint $project

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
Write-Host ""

# Deactivate the environment if it was not active

if (-not $isVirtualEnvActive) {
    deactivate
}
