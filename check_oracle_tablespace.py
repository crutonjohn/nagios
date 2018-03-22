#!/usr/bin/python

import os
import cx_Oracle
import argparse
import time

#declare variables
status = ['OK:', 'WARNING:', 'CRITICAL:', 'UNKNOWN:']

#add arguments
parser = argparse.ArgumentParser()
parser.add_argument('-C', '--connector', required=True, type=str, help='connection string in USER/PASSWORD@DATABASE format')
parser.add_argument('-T', '--tablespace', required=True, type=str, help='name of the tablespace you wish to check')
parser.add_argument('-w', '--warning', default=80, type=int, help='warning threshold percent. default 80')
parser.add_argument('-c', '--critical', default=90, type=int, help='critical threshold percent. default 90')
parser.add_argument('-t', '--timeout', default=30, type=int, help='check timeout in seconds. default 30')

#parse arguments into array
args = parser.parse_args()

#assign our arguments to variables
connector	=	args.connector
tablespace	=	args.tablespace
warning 	=	args.warning
critical	=	args.critical
timeout		=	args.timeout

if not warning <= critical:
    print('The warning threshold must be less than or equal to the critical threshold')
    exit(3)

#these environment variables need to be set either within the script,
#	or within the OS (system or user level)
#os.putenv('ORACLE_HOME', '/usr/lib/oracle/12.1/client64')
#os.putenv('LD_LIBRARY_PATH', '/usr/lib/oracle/12.1/client64')
	
#test connection to db using connect argument
try:
  con = cx_Oracle.connect (connector)
except cx_Oracle.DatabaseError:
	print status[3]+" check --connector argument formatting"
	printException(exception)
	exit(3)
 
#prep temp tablespace evaluation
tempeval =	"SELECT tablespace_name " \
			"FROM dba_temp_files " \
			"WHERE tablespace_name = '%s'" % tablespace

#create cursor to initiate db connection
curse = con.cursor()

#execute temp tablespace evaluation
curse.execute(tempeval)
#establish boolean for temp tablespaces
tempcount = 0
for result in curse:
	print result[0]
	if result[0] == tablespace:
		tempcount = 1
if tempcount > 0:
	#temporary tablespace has been detected WEE-WOO-WEE-WOO
	#test for auto-extensibility on temp tablespace
	#there is very little reason for a temp tablespace to be auto-extensible,
	#however it can happen.
	tbltempauto	=	"SELECT AUTOEXTENSIBLE " \
					"FROM dba_temp_files " \
					"WHERE tablespace_name = '%s'" % tablespace

	curse.execute(tbltempauto)
	for result in curse:
		if result[0] == "NO":
			#prep temp non-auto-extensible tablespace usage percentage sql
			usagesql =	"SELECT round((df.bytes-sum(fs.bytes)) * 100 / df.bytes, 2) ts_pct_used " \
						"FROM (select tablespace_name, bytes_used bytes from V$temp_space_header " \
						"group by tablespace_name, bytes_free, bytes_used) fs, " \
						"(select tablespace_name, sum(bytes) bytes, sum(decode(maxbytes, 0, bytes, maxbytes)) maxbytes " \
						"from dba_temp_files group by tablespace_name) df " \
						"WHERE fs.tablespace_name = df.tablespace_name " \
						"AND df.tablespace_name = '%s' " \
						"GROUP BY df.tablespace_name, df.bytes, df.maxbytes" % tablespace
			
			curse.execute(usagesql)
			for result in curse:
			#set var for percentage of tablespace used
				usagepct = result[0]
				con.close()
		
		elif result[0] == "YES":
			#prep temp auto-extensible tablespace usage percentage sql
			usagesql =	"SELECT round((df.bytes - sum(fs.bytes)) / (df.maxbytes) * 100, 2) max_ts_pct_used " \
						"FROM (select tablespace_name, bytes_used bytes from V$temp_space_header " \
						"group by tablespace_name, bytes_free, bytes_used) fs, " \
						"(select tablespace_name, sum(bytes) bytes, sum(decode(maxbytes, 0, bytes, maxbytes)) maxbytes " \
						"from dba_temp_files group by tablespace_name) df " \
						"WHERE fs.tablespace_name = df.tablespace_name " \
						"AND df.tablespace_name = '%s' " \
						"GROUP BY df.tablespace_name, df.bytes, df.maxbytes" % tablespace
			
			curse.execute(usagesql)
			for result in curse:
				#set var for percentage of tablespace used
				usagepct = result[0]
				con.close()
		#error handling
		else:
			print status[3]+" Unable to determine if temp tablespace %s is auto-extensible" % tablespace
			exit(3)
elif tempcount == 0:
	#tablespace isn't temporary
	#prep sql to evaluate auto-extensibility
	tblautoeval	=	"SELECT max(df.autoextensible) auto_ext " \
					"FROM dba_free_space fs, (select tablespace_name, max(autoextensible) autoextensible " \
					"from dba_data_files group by tablespace_name) df " \
					"WHERE fs.tablespace_name = df.tablespace_name AND df.tablespace_name = '%s' " \
					"GROUP BY df.tablespace_name" % tablespace
		
	#execute evaluation
	curse.execute(tblautoeval)
	for result in curse:
		if result[0] == "YES":
			#prep autoextensible query
			sqltblauto	=		"SELECT round((df.bytes - sum(fs.bytes)) / (df.maxbytes) * 100, 2) max_ts_pct_used " \
								"FROM dba_free_space fs, (select tablespace_name, sum(bytes) bytes, " \
								"sum(decode(maxbytes, 0, bytes, maxbytes)) maxbytes, max(autoextensible) autoextensible " \
								"from dba_data_files group by tablespace_name) df " \
								"WHERE fs.tablespace_name = df.tablespace_name AND df.tablespace_name = '%s' " \
								"GROUP BY df.tablespace_name, df.bytes, df.maxbytes" % tablespace
			
			curse.execute(sqltblauto)
			for result in curse:
				#set var for percentage of tablespace used
				usagepct = result[0]
				con.close()

		elif result[0] == "":
			#prep non-autoextend query
			sqltblstatic	=	"SELECT round((df.bytes-sum(fs.bytes)) * 100 / df.bytes, 2) ts_pct_used " \
								"FROM dba_free_space fs, (select tablespace_name, sum(bytes) bytes, " \
								"sum(decode(maxbytes, 0, bytes, maxbytes)) maxbytes, max(autoextensible) autoextensible " \
								"from dba_data_files group by tablespace_name) df " \
								"WHERE fs.tablespace_name = df.tablespace_name AND df.tablespace_name = '%s' " \
								"GROUP BY df.tablespace_name, df.bytes, df.maxbytes" % tablespace
			
			curse.execute(sqltblstatic)
			for result in curse:
				#set var for percentage of tablespace used
				usagepct = result[0]
				con.close()
		#error handling
		else:
			con.close()
			print status[3]+" Unable to determine if static tablespace %s is auto-extensible" % tablespace
			exit(3)
else:
	con.close()
	#error handling
	print status[3]+" Unable to determine if tablespace %s is temporary" % tablespace
	exit(3)	
#do some comparisons with the thresholds and exit accordingly
if usagepct >= critical:
	print status[2]+" {!s} usage is at {!s}%  | usage={!s};{!s};{!s}".format(tablespace, usagepct, usagepct, warning, critical)
	exit(2)
elif usagepct >= warning:
	print status[1]+" {!s} usage is at {!s}%  | usage={!s};{!s};{!s}".format(tablespace, usagepct, usagepct, warning, critical)
	exit(1)
elif usagepct < warning:
	print status[0]+" {!s} usage is at {!s}%  | usage={!s};{!s};{!s}".format(tablespace, usagepct, usagepct, warning, critical)
	exit(0)
else:
	print status[3]+" Unable to determine {!s} usage. % read as {!s}".format(tablespace, usagepct)
	exit(3)
