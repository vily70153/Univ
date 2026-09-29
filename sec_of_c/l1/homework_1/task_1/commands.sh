wc -w data.dat
grep -cE "d[ao]lor" data.dat
wc -l data.dat
grep -oE "\bdol\w" data.dat | wc -l
