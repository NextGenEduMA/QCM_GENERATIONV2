@echo off
echo Cleaning up non-essential files...

REM Create backup directory
mkdir backup_files 2>nul

REM Move test files to backup
echo Moving test files...
move test_*.py backup_files\ 2>nul
move debug_*.py backup_files\ 2>nul
move debug_*.json backup_files\ 2>nul

REM Move older versions of scripts
echo Moving older script versions...
move arabic_diacritized_qcm.py backup_files\ 2>nul
move arabic_diacritized_qcm_v2.py backup_files\ 2>nul

REM Move duplicate JSON files
echo Moving duplicate JSON files...
move "*_Copy.json" backup_files\ 2>nul

REM Move example files
echo Moving example files...
move example.py backup_files\ 2>nul

REM Move older README files
echo Moving older README files...
move README-*.md backup_files\ 2>nul

REM Move other non-essential files
echo Moving other non-essential files...
move fix_rag.py backup_files\ 2>nul
move fixed_rag_results.json backup_files\ 2>nul
move improve_question.py backup_files\ 2>nul
move improved_rag_results.json backup_files\ 2>nul
move integrate_rag_diacritized.py backup_files\ 2>nul
move integrate_rag.py backup_files\ 2>nul
move qcm_improver.py backup_files\ 2>nul
move simple_improve.py backup_files\ 2>nul
move simple_rag.py backup_files\ 2>nul

echo Cleanup complete! Non-essential files have been moved to the backup_files directory.
echo You can now run the application with: python -m uvicorn simple_app:app --host 127.0.0.1 --port 8001