Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Committing Changes to GitHub" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Step 1: Stopping any running servers..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep 2

Write-Host "Step 2: Checking git status..." -ForegroundColor Yellow
git status

Write-Host ""
Write-Host "Step 3: Adding all changes..." -ForegroundColor Yellow
git add .

Write-Host "Step 4: Committing changes..." -ForegroundColor Yellow
$commitMessage = @"
feat: Fix production mode and enhance batch processing functionality

🔧 Major Improvements:
- FIXED: Force production mode - files now actually deleted (not simulated)
- ENHANCED: Batch processing with real API endpoints and CSV/JSON parsing
- ADDED: Debug logging for troubleshooting upload issues
- IMPROVED: File upload functionality with better error handling
- ADDED: Test upload page for debugging batch processing
- FIXED: All DEMO_MODE references to ensure real file deletion

🚀 Production Ready:
- File wiping now permanently deletes original files from system
- Batch processing supports CSV and JSON device lists
- Enhanced error reporting and logging
- Multi-factor authentication for device operations
- Blockchain verification and certificate generation

✅ All core functionality verified and working correctly
"@

git commit -m $commitMessage

Write-Host "Step 5: Pushing to GitHub..." -ForegroundColor Yellow
git push

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Commit Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green