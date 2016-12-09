# kill all running python processes
kill $(ps aux | grep '[p]ython' | awk '{print $2}') &> /dev/null
echo "All running Python processes killed..."
rm -rf ./input
rm -rf ./output
echo "Old test files destroyed..."

OPTIND=1         # Reset in case getopts has been used previously in the shell.

while getopts ":nm" opt; do
    case $opt in
    n)  echo "Stored filesystem data destroyed..." && rm -rf ./nodefiles/*
        ;;
    m)  rm -rf ./registrydata/*
        echo "Stored records for master node destroyed..."
        ;;
    esac
done

echo ""
echo "Ready to go."
