#!/bin/sh

# network
docker network create influxdb

# InfluxDB (database)
docker run -d --name influxdb --net=influxdb -p 8083:8083 -p 8086:8086 influxdb

# Telgraf (Aggregator)
docker run -d --name telegraf --net=influxdb -v$PWD/scripts:/scripts:ro -v$PWD/telegraf.conf:/etc/telegraf/telegraf.conf:ro gocd_telegraf

# Chronograf (UI)
docker run -d --name chronograf --net=influxdb -p 10000:10000 chronograf

# cAdvisor
sudo docker run --name=cadvisor --net=influxdb --volume=/:/rootfs:ro --volume=/var/run:/var/run:rw --volume=/sys:/sys:ro --volume=/var/lib/docker/:/var/lib/docker:ro --publish=8080:8080 --detach=true --link influxdb:influxsrv google/cadvisor:latest -storage_driver_db=cadvisor -storage_driver_host=influxdb:8086 -storage_driver=influxdb

# # Grafana
# sudo docker run -d  --name grafana --net=influxdb -p 3000:3000 -e INFLUXDB_HOST=influxdb -e INFLUXDB_PORT=8086 -e INFLUXDB_NAME=cadvisor -e INFLUXDB_USER=root -e INFLUXDB_PASS=root --link influxdb:influxsrv grafana/grafana
