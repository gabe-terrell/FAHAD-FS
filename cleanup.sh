# kill all running python processes
kill $(ps aux | grep '[p]ython' | awk '{print $2}')
rm -r ./nodefiles/*
mkdir nodefiles
mkdir registrydata
