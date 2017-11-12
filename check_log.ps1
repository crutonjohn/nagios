#Search log for string and return count of occurrances
#Variable $eventstring implies use of "Where-Object -like"
#Written by Curtis John or whatever

# Process arguments and declare variables
[CmdletBinding()]
Param(
	# Specify the filename of the desired log, NOT the path/directory
	[Parameter(Mandatory=$True)][string]$filename,
	
	# Specify the directory of the desired log
	[Parameter(Mandatory=$True)][string]$directory,
	
	# Specify the desired search string
	[Parameter(Mandatory=$True)][string]$eventstring,
	
	# Specify the number of events to throw warning flag
	[Parameter(Mandatory=$True)][int]$warning,
	
	# Specify the number of events to throw critical flag
	[Parameter(Mandatory=$True)][int]$critical
)

#needs to be set to false to have the chance to fail try/catch
$logexist =  $false
#concatenate $directory and $filename
$loglocation = "${directory}${filename}"


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

#grab log information and set it as a variable
$filteredlog = (get-content $loglocation)
#filter the log for our variable
$filteredlog | where-object {$_ -like "$eventstring"} -outvariable yeet | Out-Null
#set count of matching events to a useable variable
$yeetcount = $yeet.count

#search log for number of events in the past $time minutes
if ($logexist = $true)
	{
			#equal to zero events is good
		if ($yeetcount -eq 0)
			{
				$output = "OK: No matching events detected"
				$status = 0
						
			}
			#greater than or equal to $critical events 
		elseif ($yeetcount -ge $critical)
			{
				$output = "CRITICAL: ${yeetcount} matching events detected"
				$status = 2
			
			}
			#greater than or equal to $warning events
		elseif ($yeetcount -ge $warning)
			{
				$output = "WARNING: ${yeetcount} matching events detected"
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
		$output = "CRITICAL: logfile cannot be located!"
		$status = 2
	
	}

#print dat sweet sweet exit code
Write-Host $output
Exit $status
