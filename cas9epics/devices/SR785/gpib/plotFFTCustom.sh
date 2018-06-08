t=$(date +%H%M)
command="python plotFFT.py --title $t -r -v 50 -b 12kHz"
$command

