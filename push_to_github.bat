@echo off
echo ========================================
echo Push to GitHub QUANTALPHA Repository
echo ========================================
echo.

echo [1/4] Checking Git status...
git status
echo.

echo [2/4] Adding all files...
git add -A
echo.

echo [3/4] Committing changes...
git commit -m "Complete Alpha-Mining LLM Agent Framework with hedge fund research workflow

- Professional research process: hypothesis -> design -> backtest -> analysis -> documentation
- Momentum factors prioritized throughout all agents (Sharpe >= 1.8, MaxDD <= -25%)
- Comprehensive analysis guidelines (performance, stability, risk, regime, decay, sample quality)
- End-to-end pipeline: generate alpha factors and evaluation reports
- Production-ready with error handling, logging, monitoring, backup/recovery
- Complete documentation and testing framework
- All components verified and working"
echo.

echo [4/4] Pushing to GitHub...
git push -u upstream main
echo.

echo ========================================
echo Push complete!
echo Repository: https://github.com/WenyuChiou/QUANTALPHA
echo ========================================
pause
