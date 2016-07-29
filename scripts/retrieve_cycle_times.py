#!/usr/bin/env python
#
# This dirty little script pulls in pipeline & stage timings from GoCD
# NOTE: Start/End times are milliseconds since the epoch.  Duration is also milliseconds.
#
from __future__ import print_function
import click
import requests
import time
import sys

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

# Global state [sucks]
gocd_session = requests.Session()
gocd_host = 'http://build.go.cd'

def initialize_gocd(username, password, host):
    global gocd_session
    global gocd_host
    gocd_session.auth = (username,password)
    gocd_host = host
    r = gocd_session.get(_url('/go/api/dashboard'),headers={'Accept': 'application/vnd.go.cd.v1+json'})
    r.raise_for_status()

    return


def _url(path):
    return gocd_host + path

def get_pipeline_execution(counter='latest'):
    pass

def find_good_runs(pipelines,max_depth,exclude_stage):
    # Build a running list of stages that passed, and a running list of stages that didn't.
    good_runs=list()
    for run in pipelines:
        for stage in run['stages']:
            if (stage['name'] in exclude_stage ) or (not stage['scheduled']) or (stage['result'] != u'Passed'):
                continue
            if good_runs == None:
                good_runs = list(run['counter'])
            else:
                if run['counter'] not in good_runs:
                    good_runs.append(run['counter'])
            if len(good_runs) >= max_depth:
                return(good_runs)

    if len(good_runs) > 0:
        return good_runs

    return None


# retrieve a list of pipeline runs that were good, up to a limit of max_depth.
#
def get_pipeline_successes(pipeline,max_depth,exclude_stage):
    retval = None
    r = gocd_session.get(_url("/go/api/pipelines/%s/history" % pipeline))
    if r.status_code != 200:
        raise Exception("Cannot retrieve pipeline %s history." % pipeline)

    # Scan the last few executions
    retval = find_good_runs(r.json()['pipelines'],max_depth,exclude_stage)

    if retval == None or len(retval) < max_depth:
        # No recent passing run.  Walk the history backwards.
        max_counter = r.json()['pagination']['total']
        page_size = r.json()['pagination']['page_size']
        offset = page_size
        while offset < max_counter:
            r = gocd_session.get(_url("/go/api/pipelines/%s/history/%i" % (pipeline,offset)))
            if r.status_code != 200:
                raise Exception("Cannot retrieve pipeline %s history." % pipeline)
            # check the next page
            if retval == None:
                found = 0
            else:
                found = len(retval)
            new_matches = find_good_runs(r.json()['pipelines'],max_depth-found,exclude_stage)
            if new_matches != None:
                try:
                    retval += new_matches
                except TypeError:
                    retval = new_matches

            # stop if we've hit max depth or have exhausted our list
            if (retval != None and len(retval) >= max_depth) or (len(r.json()['pipelines']) < page_size):
                break

            offset+=page_size
            if offset > max_counter:
                offset = max_counter

    return retval

def get_stages_first_schedule(stages):
    retval = None
    # There's no log of when a pipeline, or stage, is triggered.
    # The best we can do is find the starting time of the earliest job
    first_schedule = int(time.time()*1000)
    for stage in stages:
        for job in stage['jobs']:
            if job['scheduled_date'] < first_schedule:
                retval = first_schedule = job['scheduled_date']

    return retval

def get_stage_ms_timing(pipeline,pcounter,stage,scounter):
    start=int(time.time()*1000)
    end=0
    stage_url = "/go/api/stages/%s/%s/instance/%s/%s" % (pipeline,stage,pcounter,scounter)
    sinst = gocd_session.get(_url(stage_url))

    if sinst == None:
        return None

    for job in sinst.json()['jobs']:
        for state in job['job_state_transitions']:
            if state['state_change_time'] < start:
                start = state['state_change_time']
            if state['state_change_time'] > end:
                end = state['state_change_time']
    if start > end:
        start=end=0
    return (start,end,end-start)

@click.command()
@click.option('--max-depth', '-d', envvar='GOCD_METRICS_DEPTH', default=1, type=click.IntRange(0,9999),help='Maximum number of pipeline executions to retrieve. 0 indicates unlimited, default is 1. This value applies per pipeline.')
@click.option('--pipeline','-P', envvar='GOCD_METRICS_PIPELINES', type=click.STRING, multiple=True, help="Pipeline to retrieve. Default is all. Can be specified multiple times: -p foo -p bar")
@click.option('--exclude-stage','-x', envvar='GOCD_METRICS_EXCLUDE', type=click.STRING, multiple=True, help="Ignore stages named TEXT in any pipeline. Useful for stages that handle exception conditions - rollback for example. Can be specified multiple times: -x foo -x bar")
@click.option('--username','-u', envvar='GOCD_METRICS_USERNAME', default='view', type=click.STRING, help="User to authenticate as.")
@click.option('--password','-p', envvar='GOCD_METRICS_PASSWORD', default='password', type=click.STRING, help="Password to authenticate with.")
@click.option('--host','-H', envvar='GO_SERVER_URL', default='http://build.go.cd', type=click.STRING, help="URL of GoCD server host to use. e.x. http://build.go.cd")
def retrieve_gocd_metrics(max_depth,pipeline,exclude_stage,username,password,host):
    initialize_gocd(username, password, host)
    # If they've requested unlimited history we actually stop at maxint
    if max_depth==0:
        max_depth=sys.maxint
        eprint("INFO please wait as we gather data for ALL passing pipelines.  expect some delay.")
    else:
        eprint("INFO please wait as we gather data for %d passing pipelines." % max_depth)

    source_list = list(pipeline)
    if not source_list:
        # Retrieve a list of all pipelines.  You have to get all groups, then extract the pipelines
        r = gocd_session.get(_url('/go/api/config/pipeline_groups'))
        if r.status_code == 200:
            # List of all pipeline groups
            for group in r.json():
                # List of all pipelines
                for found in group['pipelines']:
                    source_list.append(found['name'])

    for pipeline in source_list:
        pipeline_successes = get_pipeline_successes(pipeline,max_depth,exclude_stage)
        for counter in pipeline_successes:
            first_mod_time=pl_start = int(time.time()*1000)
            pl_end = 0
            # If it ran grab the details from the execution instance
            pipeline_url = "/go/api/pipelines/%s/instance/%s" % (pipeline,counter)
            run = gocd_session.get(_url(pipeline_url))
            # find first modification time
            for matrev in run.json()['build_cause']['material_revisions']:
                for mod in matrev['modifications']:
                    if mod['modified_time'] < first_mod_time:
                        first_mod_time=mod['modified_time']

            first_schedule = get_stages_first_schedule(run.json()['stages'])
            for stage in run.json()['stages']:
                if stage['name'] not in exclude_stage:
                    (start,end,duration) = get_stage_ms_timing(pipeline,run.json()['counter'],stage['name'],stage['counter'])
                    print("stage_cycle_time,pipeline=%s,pipeline_counter=%d,stage=%s,stage_counter=%s start=%di,end=%di,duration=%di,change=%di,duration_from_change=%di %d" % (pipeline,counter,stage['name'],stage['counter'],start,end,duration,first_mod_time,end-first_mod_time,end*1000000))
                    if start < pl_start:
                        pl_start = start
                    if end > pl_end:
                        pl_end = end
            print("pipeline_cycle_time,pipeline=%s,pipeline_counter=%d start=%di,end=%di,duration=%di,change=%di,duration_from_change=%di %d" % (pipeline,counter,pl_start,pl_end,pl_end-pl_start,first_mod_time,end-first_mod_time,pl_end*1000000))

if __name__ == '__main__':
    retrieve_gocd_metrics()
