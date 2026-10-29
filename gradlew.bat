@echo off
setlocal
set "ROOT=%~dp0"
set "WRAPPER=%ROOT%gradle\wrapper\gradle-wrapper.jar"
if not exist "%WRAPPER%" (
  echo Downloading verified Gradle 8.13 wrapper JAR (first run only)...
  powershell -NoProfile -ExecutionPolicy Bypass -Command "$u='https://services.gradle.org/distributions/gradle-8.13-wrapper.jar';$f='%WRAPPER%';Invoke-WebRequest -Uri $u -OutFile $f; $expected='81a82aaea5abcc8ff68b3dfcb58b3c3c429378efd98e7433460610fecd7ae45f'; $actual=(Get-FileHash -Algorithm SHA256 $f).Hash.ToLowerInvariant();if($actual -ne $expected){Remove-Item $f -ErrorAction SilentlyContinue;throw 'Wrapper SHA256 mismatch'}"
  if errorlevel 1 exit /b 1
)
if defined JAVA_HOME (
  "%JAVA_HOME%\bin\java.exe" -cp "%WRAPPER%" org.gradle.wrapper.GradleWrapperMain %*
) else (
  java -cp "%WRAPPER%" org.gradle.wrapper.GradleWrapperMain %*
)
endlocal
