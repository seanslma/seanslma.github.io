@echo off

REM migrate MySQL to MSSQL

setlocal EnableDelayedExpansion 

set dir=%~dp0
set src="%dir%ConversionAndDataMigration_tbl.xml"
set var="%dir%VariableValueFile.xml"

REM set dbn=rec
REM SSMAforMySQLConsole.exe -s %src% -v %var% -v $SourceDatabase$ %dbn% -v $TargetDB$ %dbn% -v $project_name$ %dbn% -l "%log%\cli.log"

set dbn=%~1
set tbs="%dir%inp\list_%dbn%.txt"
set dtf="%dir%log\time_%dbn%.log"
set log="%dir%log\cli_%dbn%.log"

set exe="C:\Program Files\Microsoft SQL Server Migration Assistant for MySQL\bin\SSMAforMySQLConsole.exe"

set i=0
(echo %date% %time% dump tbs: %dbn%) >>%dtf% 2>&1
for /f "tokens=1-3* delims=," %%a in ('type %tbs%') do (
    set /a i=!i!+1
    (echo !date! !time!  !i! tb: %%a) >>%dtf% 2>&1
    %exe% -s %src% -v %var% -v $SourceDatabase$ %dbn% -v $TargetDB$ %dbn% -v $mysql_table$ %%a -v $ParentFolder$ %dir% -v $project_name$ %dbn%__%%a -l %log%
)

(echo %date% %time% all done!) >>%dtf% 2>&1
