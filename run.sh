#!/bin/sh

# network
docker network create influxdb

# InfluxDB (database)
docker run -d --name influxdb --net=influxdb -p 8083:8083 -p 8086:8086 influxdb

# Telgraf (Aggregator)
docker run -d --net=influxdb -v$PWD/scripts:/scripts:ro -v$PWD/telegraf.conf:/etc/telegraf/telegraf.conf:ro gocd_telegraf

# Chronograf (UI)
docker run --net=influxdb -p 10000:10000 chronograf
