#!/bin/bash

echo "🔪 Killing all Python processes..."
pkill -f python

echo "🗑️  Cleaning up port 5000..."
# Kill any process using port 5000
lsof -ti:5000 | xargs kill -9 2>/dev/null

echo "✅ Cleanup complete!"
echo "📊 Remaining Python processes:"
ps aux | grep python | grep -v grep | wc -l
echo "🔍 Port 5000 status:"
lsof -i:5000 || echo "Port 5000 is free"