# Load environment variables from .env file
Get-Content config\.env | ForEach-Object {
    if ($_ -match '^([^#][^=]+)=(.+)$') {
        $name = $matches[1].Trim()
        $value = $matches[2].Trim()
        Set-Variable -Name $name -Value $value -Scope Global
        Write-Host "Loaded: $name"
    }
}

Write-Host ""
Write-Host "Environment loaded! Your suffix is: $S3_SUFFIX"