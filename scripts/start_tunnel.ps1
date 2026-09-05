<#
.SYNOPSIS
    Terminal 2: open the public tunnel that Razorpay delivers webhooks through.

.DESCRIPTION
    WHY THIS SCRIPT EXISTS
        The tunnel command carries one value that changes per machine - the reserved
        domain - and every time it appeared in a document as a placeholder, the
        placeholder got pasted verbatim and the run failed with a DNS error that looks
        nothing like its cause. So the domain is read from .env, where it is recorded
        once, and there is nothing left in the command to substitute.

        ngrok runs inside WSL: Windows Smart App Control blocks the native binary as a
        low-reputation download. WSL mirrored networking (see C:\Users\Dell\.wslconfig)
        is what lets it reach the webhook server bound to 127.0.0.1 on Windows.

.EXAMPLE
    .\scripts\start_tunnel.ps1
#>
[CmdletBinding()]
param(
    [int]$Port = 8000,
    [string]$EnvFile = ".env",
    [string]$Distro = "Ubuntu",
    [string]$NgrokPath = "/home/astra/bin/ngrok"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $EnvFile)) {
    throw "$EnvFile not found. Copy .env.example to .env first."
}

# Read NGROK_DOMAIN out of .env rather than taking it as an argument: an argument is a
# placeholder waiting to be pasted wrong, a recorded value is not.
$domain = $null
foreach ($line in Get-Content $EnvFile) {
    if ($line -match '^\s*NGROK_DOMAIN\s*=\s*(.+?)\s*$') { $domain = $Matches[1].Trim() }
}

if ([string]::IsNullOrWhiteSpace($domain)) {
    Write-Host ""
    Write-Host "NGROK_DOMAIN is not set in $EnvFile." -ForegroundColor Yellow
    Write-Host "Claim your free static domain at https://dashboard.ngrok.com/domains"
    Write-Host "then add this line to $EnvFile (with YOUR domain, not this text):"
    Write-Host ""
    Write-Host "    NGROK_DOMAIN=something-random-1234.ngrok-free.app" -ForegroundColor Cyan
    Write-Host ""
    exit 1
}

# The exact failure this script exists to prevent.
if ($domain -match 'YOUR|EXAMPLE|CHANGEME|something-random|<|>') {
    throw "NGROK_DOMAIN in $EnvFile is still a placeholder ('$domain'). Put your real ngrok domain there."
}

# ngrok 3.39 deprecated --domain in favour of --url, which wants a full origin.
$url = "https://$domain"

Write-Host ""
Write-Host "Tunnel      $url" -ForegroundColor Green
Write-Host "Forwarding  -> http://localhost:$Port"
Write-Host "Webhook URL $url/webhooks/razorpay" -ForegroundColor Cyan
Write-Host ""
Write-Host "Register that webhook URL in Razorpay ONCE. A reserved domain does not"
Write-Host "change when this process restarts, so it never needs updating again."
Write-Host ""
Write-Host "Leave this window open for the whole demo. Ctrl+C closes the tunnel."
Write-Host ""

wsl -d $Distro -- $NgrokPath http $Port --url=$url
