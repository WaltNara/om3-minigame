param(
    [string]$CardRoot,
    [ValidateSet('Install', 'Restore')][string]$Mode = 'Install'
)
$ErrorActionPreference = 'Stop'
try {
    $packageRoot = $PSScriptRoot
    $checks = @{}
    foreach ($line in Get-Content -LiteralPath (Join-Path $packageRoot 'SHA256SUMS')) {
        if ($line -notmatch '^([0-9a-f]{64})  (.+)$') { throw 'Malformed SHA256SUMS' }
        $expected = $Matches[1]
        $relative = $Matches[2]
        $file = Join-Path $packageRoot $relative
        if ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -ne $expected) {
            throw "Package hash mismatch: $relative"
        }
        $checks[$relative] = $expected
    }
    Write-Host "PASS: $($checks.Count) package files match SHA256SUMS."
    if ($CardRoot) {
        $cardPath = (Resolve-Path -LiteralPath $CardRoot).Path
        $copies = if ($Mode -eq 'Install') {
            @('card/DCOLYMP/E1479999.BIN', 'card/OM3MOD/GUIDES.BIN',
              'card/OM3MOD/LABELS.BIN', 'card/OM3MOD/TONES.BIN')
        } else { @('restore/DCOLYMP/E1479999.BIN') }
        foreach ($source in $copies) {
            if (-not $checks.ContainsKey($source)) { throw "Missing checksum: $source" }
            $target = Join-Path $cardPath ($source -replace '^[^/]+/', '')
            if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ne $checks[$source]) {
                throw "Card file does not match $Mode image/data: $target"
            }
        }
        Write-Host "PASS: firmware and required data match $Mode. This verifies bytes only, not the body model/version or hardware safety."
    }
} catch {
    Write-Error $_ -ErrorAction Continue
    exit 1
}
