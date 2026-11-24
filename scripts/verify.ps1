$ErrorActionPreference = 'Stop'
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    foreach ($name in 'user-service', 'loan-service', 'payment-service') {
        docker compose exec -T $name python -m pytest -q -p no:cacheprovider tests
        if ($LASTEXITCODE -ne 0) { throw "$name tests failed" }
    }
    docker compose run --rm --no-deps -e F168_GATEWAY_URL=http://gateway:8080 -v "./tests:/checks:ro" user-service python -m pytest -q -p no:cacheprovider /checks/test_gateway.py
    if ($LASTEXITCODE -ne 0) { throw 'Gateway tests failed' }
} finally { Pop-Location }
