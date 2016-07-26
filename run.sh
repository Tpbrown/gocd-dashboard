#!/bin/sh

# Data storage container
docker run -d --name influxdb -p 8083:8083 -p 8086:8086 influxdb

# Telgraf
docker run -d --net=container:influxdb telegraf:1.0.0-beta3-alpine
