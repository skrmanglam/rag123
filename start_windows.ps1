param(
    [string]$CondaEnv = "rag123"
)

$ErrorActionPreference = "Stop"

Write-Host "=================================="
Write-Host "RAG Chatbot Builder - Startup"
Write-Host "=================================="
Write-Host ""

if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found!"
    Write-Host "Creating .env from .env.example..."
    Copy-Item ".env.example" ".env"
    Write-Host "✅ Created .env file"
}

if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")){
            $parts = $line -split("="), 2
            [System.Environment]::SetEnvironmentVariable($parts[0], $parts[1])
        }
    }
}

$settingsContent = Get-Content "config/settings.yaml"
$providerLine = $settingsContent | Select-String "provider: \s*" | Select-Object -First 1
$LLM_PROVIDER = "ollama"
if ($providerLine) {
    $LLM_PROVIDER = ($providerLine.Matches[0].Value -replace 'provider:\s*"|"','').Trim()
}

Write-Host "LLM Provider: $LLM_PROVIDER"

if ($LLM_PROVIDER -eq "openai") {
    if (-not $env:OPENAI_API_KEY) {
        Write-Host "❌ OPENAI_API_KEY is not set!"
        Write-Host "Please set it in .env file or export it:"
        exit 1
    }
    Write-Host "✅ OPENAI_API_KEY is set"
} elseif ($LLM_PROVIDER -eq "ollama") {
    Write-Host "✅ Using Ollama (local LLM)"
    Write-Host "   Make sure Ollama is running: ollama serve"
} else {
    Write-Host "✅ Using $LLM_PROVIDER"
}
Write-Host ""

docker info *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker is not running!"
    Write-Host "Please start Docker and try again."
    exit 1
}

Write-Host "✅ Docker is running"
Write-Host ""

Write-Host "Starting Qdrant..."
docker-compose up -d
if ($LASTEXITCODE -ne 0) {
    docker-compose up -d
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to start Qdrant with docker-compose!"
        exit 1
    }
}

Write-Host "Waiting for Qdrant to be ready..."
$qdrantReady = $false
for ($1 = 1; $i -le 30; $i++){
    try{
        Invoke-WebRequest -Uri "http://localhost:6333/" -UseBasicParsing | Out-Null
        $qdrantReady = $true
        Write-Host "Qdrant is ready"
        break
    } catch {
        Start-Sleep -Seconds 1 
    }
}
if (-not $qdrantReady){
    Write-Host "Qdrant failed to start"
    exit 1
}

Write-Host "=================================="
Write-Host "Starting Application Services"
Write-Host "=================================="
Write-Host ""

$condaCheck = Get-Command conda -ErrorAction SilentlyContinue
if (-not $condaCheck) {
    Write-Host "Conda is not available in PATH"
    Write-Host "Open Anaconda Prompt or add conda to PATH, then run this script again."
    exit 1
}

Write-Host "Launching FastAPI and Streamlit in separate Windows terminals..."
Write-Host "Conda environment: $CondaEnv"

$fastApiCommand = "conda run -n $CondaEnv python main_api.py"
$streamlitCommand = "conda run -n $CondaEnv streamlit run app_streamlit.py"

Start-Process powershell -ArgumentList "-NoExit", "-Command", $fastApiCommand
Start-Sleep -Seconds 3
Start-Process powershell -ArgumentList "-NoExit", "-Command", $streamlitCommand

Write-Host "Waiting for FastAPI to be ready..."
$fastApiReady = $false
for ($i = 1; $i -le 30; $i++){
    try{
        Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing | Out-Null
        $fastApiReady = $true
        Write-Host "FastAPi is ready at http://localhost:8000"
        break
    } catch{
        Start-Sleep -Seconds 1 
    }
}
if (-not $fastApiReady){
    Write-Host "FastAPI did not respond within the expected time."
    Write-Host "Check the opened terminal window for startup errors."
}

Write-Host "=================================="
Write-Host "Startup Complete"
Write-Host "=================================="
Write-Host ""
Write-Host "Streamlit UI: http://localhost:8501"
Write-Host "FastAPI: http://localhost:8000"
Write-Host "API Docs: https://localhost:8000/docs"
Write-Host "Qdrant: http://localhost:6333"
Write-Host ""
Write-Host "Notes:"
Write-Host " - Qdrant runs in Docker Desktop"
Write-Host " - FastAPI and Streamlit run in seprate PowerShell windows"
Write-Host " - Ollama should run on the Windows host at http://localhost:1134"
Write-Host ""
Write-Host "To Stop Qdrant Later:"
Write-Host " docker compose down"
Write-Host ""