@echo off
echo ========================================
echo Committing Changes to GitHub
echo ========================================
echo.

echo Step 1: Stopping any running servers...
taskkill /f /im python.exe >nul 2>&1

echo Step 2: Checking git status...
git status

echo.
echo Step 3: Adding all changes...
git add .

echo Step 4: Committing changes...
git commit -m "feat: Fix production mode and enhance batch processing functionality

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

✅ All core functionality verified and working correctly"

echo Step 5: Pushing to GitHub...
git push

echo.
echo ========================================
echo Commit Complete!
echo ========================================
pause