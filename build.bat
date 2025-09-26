@echo off
echo Building Expense Tracker...
pyinstaller --onefile --name expense-tracker main.py
echo Build complete! Check the dist folder.
pause
