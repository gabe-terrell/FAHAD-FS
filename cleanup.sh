# kill all running python processes
kill $(ps aux | grep '[p]ython' | awk '{print $2}')
rm -r ./nodefiles/*
rm ./registrydata/reg.data
mkdir -p nodefiles
mkdir -p registrydata
