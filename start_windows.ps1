param(

    [string]$CondaEnv = "rag123"

)



$ErrorActionPreference = "Stop"



Write-Host "=================================="

Write-Host "RAG Chatbot Builder - Startup"

Write-Host "=================================="

Write-Host ""



if (-not (Test-Path ".env")) {

    Write-Host ".env file not found — creating from .env.example..."

    Copy-Item ".env.example" ".env"

    Write-Host "Created .env file"

}



if (Test-Path ".env") {

    Get-Content ".env" | ForEach-Object {

        $line = $_.Trim()

        if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {

            $parts = $line -split("=", 2)

            [System.Environment]::SetEnvironmentVariable($parts[0], $parts[1])

        }

    }

}



$settingsContent = Get-Content "config/settings.yaml"

$providerLine = $settingsContent | Select-String 'provider:\s*' | Select-Object -First 1

$LLM_PROVIDER = "openai_compatible"

if ($providerLine) {

    $LLM_PROVIDER = ($providerLine.Line -replace '.*provider:\s*"?', '' -replace '"\s*.*', '').Trim()

}



Write-Host "LLM Provider: $LLM_PROVIDER"



if ($LLM_PROVIDER -eq "openai") {

    if (-not $env:OPENAI_API_KEY) {

        Write-Host "OPENAI_API_KEY is not set in .env"

        exit 1

    }

    Write-Host "OPENAI_API_KEY is set"

} elseif ($LLM_PROVIDER -eq "ollama") {

    Write-Host "Using Ollama — run: ollama serve"

} elseif ($LLM_PROVIDER -eq "openai_compatible") {

    if (-not $env:OPENROUTER_API_KEY -and -not $env:OPENAI_API_KEY) {

        Write-Host "Set OPENROUTER_API_KEY in .env for OpenRouter"

    } else {

        Write-Host "API key is set for openai_compatible provider"

    }

}

Write-Host ""



docker info *> $null

if ($LASTEXITCODE -ne 0) {

    Write-Host "Docker is not running. Start Docker Desktop and try again."

    exit 1

}



Write-Host "Docker is running"

Write-Host ""



Write-Host "Starting Qdrant..."

docker-compose up -d

if ($LASTEXITCODE -ne 0) {

    Write-Host "Failed to start Qdrant with docker-compose"

    exit 1

}



Write-Host "Waiting for Qdrant to be ready..."

$qdrantReady = $false

for ($i = 1; $i -le 30; $i++) {

    try {

        Invoke-WebRequest -Uri "http://localhost:6333/" -UseBasicParsing | Out-Null

        $qdrantReady = $true

        Write-Host "Qdrant is ready"

        break

    } catch {

        Start-Sleep -Seconds 1

    }

}

if (-not $qdrantReady) {

    Write-Host "Qdrant failed to start"

    exit 1

}



Write-Host "=================================="

Write-Host "Starting FastAPI + static UI"

Write-Host "=================================="

Write-Host ""



$condaCheck = Get-Command conda -ErrorAction SilentlyContinue

if (-not $condaCheck) {

    Write-Host "Conda is not available in PATH."

    Write-Host "Open Anaconda Prompt or add conda to PATH, then run this script again."

    exit 1

}



Write-Host "Launching FastAPI in a new terminal (conda env: $CondaEnv)..."

$fastApiCommand = "conda run -n $CondaEnv uvicorn main_api:app --host 0.0.0.0 --port 8000 --reload"

Start-Process powershell -ArgumentList "-NoExit", "-Command", $fastApiCommand



Write-Host "Waiting for FastAPI..."

$fastApiReady = $false

for ($i = 1; $i -le 30; $i++) {

    try {

        Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing | Out-Null

        $fastApiReady = $true

        Write-Host "FastAPI is ready at http://localhost:8000"

        break

    } catch {

        Start-Sleep -Seconds 1

    }

}

if (-not $fastApiReady) {

    Write-Host "FastAPI did not respond in time — check the opened terminal for errors."

}



Write-Host "=================================="

Write-Host "Startup complete"

Write-Host "=================================="

Write-Host ""

Write-Host "Web UI:   http://localhost:8000"

Write-Host "API Docs: http://localhost:8000/docs"

Write-Host "Qdrant:   http://localhost:6333"

Write-Host ""

Write-Host "Stop Qdrant later: docker compose down"

Write-Host ""

