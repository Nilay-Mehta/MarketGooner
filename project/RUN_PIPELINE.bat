@echo off
title Market Intelligence Engine - 1-Click Pipeline
echo ======================================================================
echo    MARKET INTELLIGENCE ENGINE (AUTONOMOUS 1-CLICK RUNNER)
echo ======================================================================
echo.
echo Target Subreddit: r/smallbusiness
echo Search Topic:     software
echo Posts to Mine:    25
echo.
echo Running full pipeline (Ingest -> Extract -> Cluster -> Laya Gate -> Word Export)...
echo.
python main.py run-all --subreddit smallbusiness --query software --limit 25
echo.
echo ======================================================================
echo Pipeline complete! Opening your Master Word Report...
echo ======================================================================
if exist output\Master_Market_Intelligence_Report.docx (
    start output\Master_Market_Intelligence_Report.docx
) else (
    echo Note: Check the output\ folder for your reports.
)
pause
