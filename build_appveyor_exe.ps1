# build_appveyor_exe.ps1

$newest_git_tag = $(git describe --abbrev=0 --tags)
$head_tag = $(git tag --points-at HEAD)

if ($head_tag) {
    $exe_name = [string]::join("", "fallingsky-", $head_tag)
} else {
    $exe_name = [string]::join("", "fallingsky-", $newest_git_tag, "post", $env:APPVEYOR_BUILD_NUMBER)
}

Start-Process -FilePath C:/Python27/Scripts/pyinstaller.exe -ArgumentList --onefile, -n, $exe_name, .\fallingsky\main.py -Wait -ErrorAction SilentlyContinue

$spec_file = [string]::join(".", $exe_name, "spec")

(Get-Content $spec_file) |
    Foreach-Object {
        if ($_ -match "PYZ") {
            "for d in a.datas:"
            "    if 'pyconfig' in d[0]:"
            "        a.datas.remove(d)"
            "        break"
        }
        if ($_ -match "console=True") {
            "          console=False )"
        } else {
            $_ # send the current line to output
        }
        if ($_ -match "pyz,") {
            #Add Lines after the selected pattern
            "          Tree('.\\fallingsky\\images', prefix='images\\'),"
        }
    } | Set-Content $spec_file

Start-Process -FilePath C:/Python27/Scripts/pyinstaller.exe -ArgumentList --onefile, -n, $exe_name, $spec_file -Wait -ErrorAction SilentlyContinue
