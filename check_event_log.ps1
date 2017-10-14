#Monitor non-standard event logs in Windows
#Written by Curtis John (2017)

# Process arguments and declare variables
[CmdletBinding()]
Param(
	# Specify the filename of the desired log, NOT the path/directory
	[Parameter(Mandatory=$True)][string]$filename,
	
	# Specify the number of events to throw warning flag
	[Parameter(Mandatory=$True)][int]$warning,
	
	# Specify the number of events to throw critical flag
	[Parameter(Mandatory=$True)][int]$critical,
	
	# Specify the desired event ID
	[Parameter(Mandatory=$True)][int]$eventid,
	
	# Specify how far back to look for events in minutes
	[Parameter(Mandatory=$False)][int]$time=15
)

#get system time
$systime = Get-Date -format G
#needs to be set to false to have the chance to fail $logexist
$logexist =  $false
#manually setting event log directory. later version will include the ability to specify a parameter for this variable
$directory = "C:\Windows\System32\Winevt\Logs\" 
#concatenate $directory and $filename
$loglocation = "${directory}${filename}"
#get time 15 minutes ago
$starttime = (Get-Date).AddMinutes(-${time})
#match date/time formatting with Get-WinEvent output
$starttime = Get-Date $starttime -format G


#assert that the log is available
try
	{
		$logexist = Test-Path "$loglocation" -PathType Leaf
		
	}
catch
	{
		Write-Host "UNKNOWN: An unknown error has occurred with the log location"
		exit 3
		
	}

#search the logs
$logrunner = Get-WinEvent -FilterHashtable @{Path="$loglocation";id=$eventid;StartTime=$starttime;EndTime=$systime} -ErrorAction silentlycontinue
#set count of matching events to a useable variable
$logrunnercount = $logrunner.count

#search log for number of events in the past $time minutes
if ($logexist = $true)
	{
			#equal to zero events is good
		if ($logrunnercount -eq 0)
			{
				$output = "OK: No matching event IDs detected in the last 15 minutes"
				$status = 0
						
			}
			#greater than or equal to $critical events 
		elseif ($logrunnercount -ge $critical)
			{
				$output = "CRITICAL: ${logrunnercount} matching event IDs detected in the last 15 minutes"
				$status = 2
			
			}
			#greater than or equal to $warning events
		elseif ($logrunnercount -ge $warning)
			{
				$output = "WARNING: ${logrunnercount} matching event IDs detected in the last 15 minutes"
				$status = 1
			
			}
			
		else
			{
				$output = "UNKNOWN: An unknown error has occurred during the enumeration of log events"
				$status = 3
				
			}
	}		

else
	{		
		$output = "CRITICAL: log file cannot be located"
		$status = 2
	
	}

#print dat sweet sweet exit code
Write-Host $output
Exit $status
