#!/bin/bash
clear
# Kill any processes running on port 50005
sudo fuser -k 50005/tcp
# Start the application
uvicorn src.app.main:app --host 0.0.0.0 --port 50005 --reload --reload-dir src
