$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$destination = Join-Path $root '.env'
$template = Get-Content (Join-Path $root '.env.example') -Raw
$rng = [Security.Cryptography.RandomNumberGenerator]::Create()
try {
    foreach ($name in 'USER_DB_PASSWORD', 'LOAN_DB_PASSWORD', 'PAYMENT_DB_PASSWORD', 'JWT_SECRET_KEY', 'INTERNAL_TOKEN') {
        $bytes = New-Object byte[] 32
        $rng.GetBytes($bytes)
        $value = [BitConverter]::ToString($bytes).Replace('-', '').ToLowerInvariant()
        $template = $template.Replace("$name=", "$name=$value")
    }
    # CreateNew stops if a teammate already created .env.
    $stream = [IO.File]::Open($destination, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
    try {
        $data = [Text.Encoding]::ASCII.GetBytes($template)
        $stream.Write($data, 0, $data.Length)
    } finally { $stream.Dispose() }
} finally { $rng.Dispose() }
Write-Host 'Created .env for local development.'
