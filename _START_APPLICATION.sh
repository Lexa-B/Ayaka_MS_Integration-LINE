#!/bin/bash
clear
uvicorn src.app.main:app --host 0.0.0.0 --port 50005 --reload --reload-dir src
