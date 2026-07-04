$ErrorActionPreference = "Stop"

Write-Host "[0/5] Preflight: dotnet available"
$dotnetInfo = dotnet --info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "dotnet --info failed. Install .NET SDK and retry."
}

Write-Host "[1/5] Restore"
dotnet restore
if ($LASTEXITCODE -ne 0) {
    Write-Error "dotnet restore failed. Check NuGet sources and credentials."
}

Write-Host "[2/5] Build"
dotnet build --configuration Release
if ($LASTEXITCODE -ne 0) {
    Write-Error "dotnet build failed. Fix compile errors before continuing."
}

Write-Host "[3/5] Test"
dotnet test --configuration Release --logger "trx;LogFileName=test-results.trx"
if ($LASTEXITCODE -ne 0) {
    Write-Error "dotnet test failed. Fix failing tests before continuing."
}

Write-Host "[4/5] Format check"
dotnet format --verify-no-changes
if ($LASTEXITCODE -ne 0) {
    Write-Error "dotnet format check failed. Run dotnet format, commit changes, then re-run verification."
}

Write-Host "[5/5] Verification PASS"
