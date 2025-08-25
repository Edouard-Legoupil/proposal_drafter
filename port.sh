# Define the ports to check
PORTS=(8502 8503)

for PORT in "${PORTS[@]}"; do
PID=$(lsof -ti tcp:$PORT)
if [ -n "$PID" ]; then
    echo "Port $PORT is in use by PID $PID. Killing process..."
    kill -9 $PID
    echo "Process $PID killed."
else
    echo "Port $PORT is not in use."
fi
done