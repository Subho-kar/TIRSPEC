#!/usr/bin/env python
""" Run this code to update the SQL database of all the observation logs in the directory """

DatabaseFilename = '~/TIRSPECDataLog.db'

LogFilename = 'SlopeimagesLog.txt'

import sqlite3
import hashlib
import shlex
import os
import sys

DataDir = sys.argv[1]
DatabaseFilename = os.path.expanduser(DatabaseFilename)  # Expand any ~
# First obtain a sorted list of immediate sub-directories which has SlopeimagesLog.txt log in it.
Directories = sorted([Dir for Dir in next(os.walk(DataDir))[1] if os.path.isfile(os.path.join(Dir,LogFilename))])

with sqlite3.connect(DatabaseFilename) as con:
    c = con.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS DirectoryTable (Directory TEXT PRIMARY KEY, md5 TEXT)')
    con.commit()
    for Dir in Directories:
        LogFileChecksum = hashlib.md5(open(os.path.join(Dir,LogFilename), 'rb').read()).hexdigest()
        D_Dir = 'D_'+Dir  # Prefixing D_ charater to make it valid table name incase directry name starts with number
        Md5Table = c.execute('SELECT md5 FROM DirectoryTable WHERE Directory = ?',(D_Dir,)).fetchone()
        if (not Md5Table) or Md5Table[0] != LogFileChecksum :
            try :
                print('Updating the log table of {0}'.format(Dir))
                c.execute('INSERT INTO DirectoryTable VALUES(?,?)',(D_Dir,LogFileChecksum))
            except sqlite3.IntegrityError:
                print('The Log file checksum was modified hence updating the table')
                c.execute('UPDATE DirectoryTable SET md5=? WHERE Directory = ?',(LogFileChecksum,D_Dir))

            # Now we proceed to create and load the new log file table    
            c.execute("DROP TABLE IF EXISTS {} ".format(D_Dir))
            c.execute("""CREATE TABLE {0:s}(fitsfile TEXT, time TEXT, target TEXT,
            ndrs INTEGER, itime REAL, upper TEXT, lower TEXT, slit TEXT, calm TEXT, 
            date TEXT, ra TEXT, dec TEXT, pid TEXT, comment TEXT)""".format(D_Dir))
            
            # Now Read the Log file
            with open(os.path.join(Dir,LogFilename), 'r') as logfile:
                Logtype = None
                for logline in logfile:
                    logline = logline.rstrip()
                    # Skip blank lines and Commented out lines with #
                    if (logline.strip() is '') or (logline[0] =='#') :
                        continue
                    LineContentList = shlex.split(logline)
                    if Logtype is None :
                        if len(LineContentList) < 14 : # Old log wihout Ra, dec and PiD
                            Logtype = 'v0'
                            print('Log Version {0}'.format(Logtype))
                        elif len(LineContentList) == 14 : # New log
                            Logtype = 'v1'
                            print('Log Version {0}'.format(Logtype))                            
                    
                    RowDataDic={}
                    RowDataDic['fitsfile'] = LineContentList[0]
                    RowDataDic['time'] = LineContentList[1]
                    RowDataDic['target'] = LineContentList[2]
                    RowDataDic['ndrs'] = int(float(LineContentList[3]))
                    RowDataDic['itime'] = float(LineContentList[4])
                    RowDataDic['upper'] = LineContentList[5].upper()
                    RowDataDic['lower'] = LineContentList[6].upper()
                    RowDataDic['slit'] = LineContentList[7].upper()
                    RowDataDic['calm'] = LineContentList[8].upper()
                    RowDataDic['date'] = LineContentList[9]
                    RowDataDic['ra'] = LineContentList[10] if Logtype == 'v1' else '-NA-'
                    RowDataDic['dec'] = LineContentList[11] if Logtype == 'v1' else '-NA-'
                    RowDataDic['pid'] = LineContentList[12] if Logtype == 'v1' else '-NA-'
                    RowDataDic['comment'] = LineContentList[13]  if Logtype == 'v1' else ' '.join(LineContentList[10:])

                    # Now write them to the databse table
                    c.execute('INSERT INTO {0:s} VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)'.format(D_Dir),(RowDataDic['fitsfile'],
                                                                                RowDataDic['time'], RowDataDic['target'],
                                                                                RowDataDic['ndrs'], RowDataDic['itime'],
                                                                                RowDataDic['upper'], RowDataDic['lower'],
                                                                                RowDataDic['slit'], RowDataDic['calm'],
                                                                                RowDataDic['date'], RowDataDic['ra'],
                                                                                RowDataDic['dec'], RowDataDic['pid'],
                                                                                   RowDataDic['comment']))

            con.commit()
        else:
            print('Table for {0} already exists in db'.format(Dir))

        
