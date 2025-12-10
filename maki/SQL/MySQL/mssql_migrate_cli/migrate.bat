@echo off

REM migrate MySQL to MSSQL

setlocal EnableDelayedExpansion 

set dir=%~dp0
set src="%dir%ConversionAndDataMigration.xml"
set var="%dir%VariableValueFile.xml"

REM set dbn=rec
REM SSMAforMySQLConsole.exe -s %src% -v %var% -v $SourceDatabase$ %dbn% -v $TargetDB$ %dbn% -v $project_name$ %dbn% -l "%log%\cli.log"

set dbs="%dir%inp\list_db.txt"
set dtf="%dir%log\time_db.log"
set log="%dir%log\cli_db.log"

set exe="C:\Program Files\Microsoft SQL Server Migration Assistant for MySQL\bin\SSMAforMySQLConsole.exe"

set i=0
(echo %date% %time% dump dbs) >>%dtf% 2>&1
for /f "tokens=1-3* delims=," %%a in ('type %dbs%') do (
    set /a i=!i!+1
    (echo !date! !time!  !i! db: %%a) >>%dtf% 2>&1
    %exe% -s %src% -v %var% -v $SourceDatabase$ %%a -v $TargetDB$ %%a -v $project_name$ %%a -v $ParentFolder$ %dir% -l %log%
)

(echo %date% %time% all done!) >>%dtf% 2>&1
