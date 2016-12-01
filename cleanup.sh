# kill all running python processes
kill $(ps aux | grep '[p]ython' | awk '{print $2}')
