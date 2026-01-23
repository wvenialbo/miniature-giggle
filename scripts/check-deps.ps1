##
## This script is used to test the dependencies of the project
##

$venv = '.venv'

$pkgs = 'mypy', 'pyright', 'ruff', 'pydoclint', `
    'coverage[toml]', 'pytest', 'xdoctest', 'jupyterlab', `
    'boto3-stubs[s3]','types-requests', "types-tqdm" `
    'setuptools', 'setuptools-scm', 'build',  'wheel', `
    'twine', 'findpydeps'

$before = 'before.txt'
$after = 'after.txt'
$dependencies = 'dependencies.txt'

$isVirtualEnvActive = $true

if (-not $env:VIRTUAL_ENV) {
    $isVirtualEnvActive = $false
    & $venv/Scripts/Activate.ps1
}

if (-not (Test-Path -Path $dependencies)) {
    python --version > $dependencies
    python -m pip --version >> $dependencies
    Add-Content -Path $dependencies -Value "--------"
    Add-Content -Path $dependencies -Value ""
}

foreach ($pkg in $pkgs) {
    python -m pip freeze > $before

    python -m pip install --upgrade $pkg
    
    $content_before = Get-Content -Path $before
    
    if ($content_before) {
        python -m pip freeze > $after
        $content_after = Get-Content -Path $after
        $content_after = $content_after | Where-Object { $_ -notin $content_before }
    }
    else {
        python -m pip freeze > $after
        $content_after = Get-Content -Path $after
    }
    
    $content_after | Add-Content -Path $dependencies
    Add-Content -Path $dependencies -Value ""
    Add-Content -Path $dependencies -Value "--------"
    Add-Content -Path $dependencies -Value ""
    
    pip uninstall -y -r $after
}

if (Test-Path -Path $before) {
    Remove-Item $before
    Remove-Item $after
}

if (-not $isVirtualEnvActive) {
    deactivate
}
