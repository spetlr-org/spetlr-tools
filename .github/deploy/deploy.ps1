# This is the script that creates the entire deployment
# for readability it is split up into separate steps
# where we try to use meaningful names.
param (
  [Parameter(Mandatory=$true)]
  [ValidateNotNullOrEmpty()]
  [string]
  $tenantId,

  [Parameter(Mandatory=$true)]
  [ValidateNotNullOrEmpty()]
  [string]
  $pipelineClientId,

  [Parameter(Mandatory=$true)]
  [ValidateNotNullOrEmpty()]
  [string]
  $pipelineSecret,

  [Parameter(Mandatory=$false)]
  [string]
  $uniqueRunId=''
)

# import utility functions
. "$PSScriptRoot\Utilities\all.ps1"

###############################################################################################
# Execute steps in order
###############################################################################################

Get-ChildItem "$PSScriptRoot/steps" -Filter *.ps1 | Sort-Object name | Foreach-Object {
  Write-Host "###### Now running step $_"
  . ("$_")
}