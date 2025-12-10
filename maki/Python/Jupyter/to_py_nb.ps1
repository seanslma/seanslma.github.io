# convert .ipynb to .py files
# convert .py to .ipynb files, if not specify the original .ipynb files should exist
# requirement: install jupytext in base env
param (
    [switch]$py,
    [switch]$nb,
    [string[]]$files
)

function convert_to {
    param (
        [bool]$py,
        [bool]$nb,
        [string[]]$files
    )

    if ($py -and $nb) {
        Write-Output "Can only set one of -py and -nb flags"
        return
    }
    elseif (-not($py) -and -not($nb)) {
        Write-Output "At least one of -py and -nb flags should be set"
        return
    }
    if ($py) {
        $ext_from = ".ipynb"
        $ext_to = ".py"
    }
    elseif ($nb) {
        $ext_from = ".py"
        $ext_to = ".ipynb"
    }

    foreach ($file in $files) {
        $file_from = "${file}${ext_from}"
        if (Test-Path -Path "$file_from" -PathType Leaf) {
            $file_to = "${file}${ext_to}"
            Write-Output "Converting <file>${ext_from} to: ${file_to}"
            jupytext --to notebook "$file_from" > $null
        }
        else {
            Write-Output "Error: File does not exist: ${file_from}"
        }
    }
}

$msg = 'All .ipynb files will be overwritten! Continue? (Yes/no) [y]'
$response = Read-Host -Prompt $msg
if ($response -match "(^$|^y(es)?$)") {
    $cur_dir = Get-Location
    $filenames = @()
    if ($($files.Count) -gt 0) {
        foreach ($file in $files) {
            $filenames += Join-Path -Path "$cur_dir" -ChildPath "$file"
        }
    }
    else {
        $files = Get-ChildItem $cur_dir -Recurse -Exclude ".ipynb_checkpoints" -Filter "*.ipynb"
        foreach ($file in $files) {
            $filenames += Join-Path -Path "$($file.DirectoryName)" -ChildPath "$($file.BaseName)"
        }
    }
    convert_to -py $py -nb $nb -files $filenames
}
Write-Output "Done!"
