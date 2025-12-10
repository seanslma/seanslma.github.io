import os
import sys
import MySQLdb
import numpy as np
import pandas as pd
from datetime import datetime

'''
change values to '1900-01-01%' 
  for table cols with non-null datetime value '0000-00-00%'
'''

tblfile = r'C:\mssql\migrate_tmp\dtzero_tbls.csv'
logpath = r'C:\mssql\migrate_tmp\dtzero_tbls.log'

def main(argv):
    cnn = sql_cnn()
    df_tbls = load_tbls(tblfile)
    for rw in df_tbls.itertuples(index=False):
        dbn = rw.table_schema
        tbl = rw.table_name
        col = rw.column_name
        val = rw.column_default
        update_tbl(cnn, dbn, tbl, col, val)
    cnn.close()
    log(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} done')

def log(msg):
    print(msg)
    if logpath != '':
        with open(logpath, 'a+') as logfile:
            logfile.write(msg + '\n')

def sql_cnn():
    par = ['mysql.svr',3306,'usr','pwd']
    return MySQLdb.connect(host=par[0],port=par[1],user=par[2],passwd=par[3],db='',connect_timeout=300) #sec

def run_qry(cnn, qry):
    try:
        cursor = cnn.cursor()
        rows_affected = cursor.execute(qry)
        cursor.close()
    except:
        rows_affected = 0
    return rows_affected

def update_tbl(cnn, dbn, tbl, col, val):
    #change datatime to 1900-01-01 00:00:00
    va2 = '1900-01-01' + val[10:]
    qry = f'''
        update `{dbn}`.`{tbl}` set `{col}` = '{va2}' where `{col}` = '{val}';
    '''
    rows_affected = run_qry(cnn, qry)
    log(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} updated: {rows_affected:<3}  dbn:{dbn}, tbl:{tbl}, col:{col}')

def load_tbls(file):
    df = pd.read_csv(file)
    return df.rename(columns=str.lower)

if __name__ == '__main__':
    main(sys.argv)
