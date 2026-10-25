@echo off
echo Checking Ollama API at http://127.0.0.1:11434/api/tags
curl -s http://127.0.0.1:11434/api/tags
echo.
echo If no model appears, open Command Prompt and run: ollama pull llama3.2:3b
pause
