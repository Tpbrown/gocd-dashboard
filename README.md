# gocd-dashboard
Basic ops dashboard for GoCD using Telegraf, InfluxDB, and Chronograf.

Includes three scripts for gathering data.
- scripts/job_queue.sh -- Provides the queue depth of jobs waiting to be scheduled.  Indicates you don't have enough agents.
- scripts/agent_health.sh -- Provides metrics on the number of agents that aren't working. 
- scripts/retrieve_cycle_times.py -- Provides cycle time metrics on Pipelines (end to end), and Stages.  

## retrieve_cycle_times.py
```
Options:
  -d, --max-depth INTEGER RANGE  Maximum number of pipeline executions to retrieve. 0 indicates unlimited, default is
                                 1. This value applies per pipeline.
  -p, --pipeline TEXT            Pipeline to retrieve. Default is all. Can be specified multiple times: -p foo -p bar
  -x, --exclude-stage TEXT       Ignore stages named TEXT in any pipeline. Useful for stages that handle exception
                                 conditions - rollback for example. Can be specified multiple times: -x foo -x bar
  ```
  
### Typical usage
- invoke scripts/retrieve_cycle_times.py on a regular basis with no --max-depth specified. 
- Create an initial data load: ```scripts/retrieve_cycle_times.py --max-depth 0>bulk_data.txt```, then load via InfluxDB admin UI.

# Known issues
- GoCD host and credentials are hard-coded to http://build.go.cd.  They'll be extracted to ENV vars.
