# gocd-dashboard
Basic ops dashboard for GoCD using Telegraf, InfluxDB, and Chronograf.

Includes three scripts for gathering data.
- scripts/job_queue.sh -- Provides the queue depth of jobs waiting to be scheduled.  Indicates you don't have enough agents.
- scripts/agent_health.sh -- Provides metrics on the number of agents that aren't working.
- scripts/retrieve_cycle_times.py -- Provides cycle time metrics on Pipelines (end to end), and Stages. Output is [InfluxDB line protocol](https://docs.influxdata.com/influxdb/latest/write_protocols/line/).

## retrieve_cycle_times.py
```
Options:
  -d, --max-depth INTEGER RANGE  Maximum number of pipeline executions to retrieve. 0 indicates unlimited, default is
                                 1. This value applies per pipeline.
  -p, --pipeline TEXT            Pipeline to retrieve. Default is all. Can be specified multiple times: -p foo -p bar
  -x, --exclude-stage TEXT       Ignore stages named TEXT in any pipeline. Useful for stages that handle exception
                                 conditions - rollback for example. Can be specified multiple times: -x foo -x bar
  ```
## Sample output
```./scripts/retrieve_cycle_times.py -p build-linux``` :
```
stage_cycle_time,pipeline=build-linux,pipeline_counter=1108,stage=build-non-server,stage_counter=1 start=1469777411530i,end=1469777960918i,duration=549388i,change=1469777264000i,duration_from_change=696918i 1469777411530000000
stage_cycle_time,pipeline=build-linux,pipeline_counter=1108,stage=build-server,stage_counter=1 start=1469777960991i,end=1469780344707i,duration=2383716i,change=1469777264000i,duration_from_change=3080707i 1469777960991000000
pipeline_cycle_time,pipeline=build-linux,pipeline_counter=1108 start=1469777411530i,end=1469780344707i,duration=2933177i,change=1469777264000i,duration_from_change=3080707i 1469777411530000000  
```
The format is **measurement**,\[**tag=value**,tag=value,...\] **field=value**,field=value,... **timestamp**.  For specifics please refer to [InfluxDB line protocol](https://docs.influxdata.com/influxdb/latest/write_protocols/line/).

#### Measurements:
 - **stage_cycle_time** data representing a single stage execution
 - **pipeline_cycle_time** data representing a pipeline execution (including stages)

#### Fields:
 - **start** time when pipeline/stage was scheduled to execute
 - **end** time when pipeline/stage was completed, including publishing of results
 - **change** time of _earliest_ change in the modification list
 - **duration** end - start.  **_This represents cycle time from schedule to complete._**
 - **duration_from_change** end - change.  **_This represents cycle time from _change_ to complete._**

#### Timestamp:
 - The measurement timestamp is the end time in nanoseconds
 - All other time fields are millisecond precision.
 - All times are epoch time.

### Typical usage
- invoke scripts/retrieve_cycle_times.py on a regular basis with no --max-depth specified.
- Create an initial data load: ```scripts/retrieve_cycle_times.py --max-depth 0>bulk_data.txt```, then load via InfluxDB admin UI.

# Known issues
- GoCD host and credentials are hard-coded to http://build.go.cd.  They'll be extracted to ENV vars.
- No caching/eTag support yet; each sampling can be a duplicate of the last
