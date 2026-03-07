@echo off
echo Installing required packages...
python -m pip install flask boto3 awscli

echo.
echo Configuring AWS credentials...
echo Please enter your AWS Access Key ID: 
set /p AWS_ACCESS_KEY_ID=
setx AWS_ACCESS_KEY_ID %AWS_ACCESS_KEY_ID%

echo Please enter your AWS Secret Access Key: 
set /p AWS_SECRET_ACCESS_KEY=
setx AWS_SECRET_ACCESS_KEY %AWS_SECRET_ACCESS_KEY%

setx AWS_REGION ap-south-1

echo.
echo Setup complete! Run 'python app.py' to start the application.
pause
