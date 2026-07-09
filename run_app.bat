@echo off
cd /d "%~dp0"
echo 필요한 패키지를 설치합니다...
pip install -r requirements.txt
echo.
echo 앱을 실행합니다. 잠시 후 브라우저가 자동으로 열립니다.
echo 열리지 않으면 아래 주소를 직접 브라우저에 입력하세요: http://localhost:8501
echo.
python -m streamlit run app.py
pause
