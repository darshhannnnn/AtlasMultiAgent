#!/bin/bash

echo "🔄 Restarting Nass Agent System..."
echo ""

./stop.sh
sleep 2
./start.sh
