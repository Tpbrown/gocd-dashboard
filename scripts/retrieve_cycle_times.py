#!/usr/bin/env python
#
# This dirty little script pulls in pipeline & stage timings from GoCD
#
from __future__ import print_function
import requests
import time
import sys

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def _url(path):
    return 'http://build.go.cd' + path

def get_pipeline_execution(counter='latest'):
    pass

def find_good_run_in_page(pipelines,ignored_stages=None):
    # Build a running list of stages that passed, and a running list of stages that didn't.
    stages_pass=dict()
    stages_notpass=dict()
    for run in pipelines:
        good_run = True
        for stage in run['stages']:
            # Just skip any ignored stages
            if ignored_stages != None and stage['name'] in ignored_stages:
                continue

            if not stage['scheduled'] or stage['result'] != u'Passed':
                stages_notpass[stage['name']]=True
                good_run = False
                continue
            else:
                stages_pass[stage['name']]=True

        if good_run:
            return(run['counter'])

    # No passing full pipeline runs (all stages) found
    # Whittle the notpass list down to those stages who have never passed.
    for stage in stages_notpass.keys():
        if stage in stages_pass:
            stages_notpass.pop(stage)
    # Try again, but ignore those stages.  This is useful for manual gates -- like a rollback that's never occurred.
    eprint("WARNING no %s pipeline executions found with all stages passing.  Trying again but ignoring %s." % (pipelines[0]['name'],stages_notpass.keys()))
    return find_good_run_in_page(pipelines,stages_notpass)

def get_pipeline_last_passed(pipeline):
    retval = None
    r = requests.get(_url("/go/api/pipelines/%s/history" % pipeline), auth=('view','password'))
    if r.status_code != 200:
        raise Exception("Cannot retrieve pipeline %s history." % pipeline)

    # Scan the last few executions
    retval = find_good_run_in_page(r.json()['pipelines'])

    if retval == None:
        # No recent passing run.  Walk the history backwards.
        max_counter = r.json()['pagination']['total']
        page_size = r.json()['pagination']['page_size']
        offset = page_size
        while offset <= max_counter:
            r = requests.get(_url("/go/api/pipelines/%s/history/%i" % (pipeline,offset)), auth=('view','password'))
            if r.status_code != 200:
                raise Exception("Cannot retrieve pipeline %s history." % pipeline)
            # check the next page
            retval = find_good_run_in_page(r.json()['pipelines'])
            if retval != None:
                break

            offset+=10
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
    sinst = requests.get(_url(stage_url), auth=('view','password'))

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

def retrieve_gocd_metrics():
    r = requests.get(_url('/go/api/config/pipeline_groups'), auth=('view','password'))
    if r.status_code == 200:
        for group in r.json():
            for pipeline in group['pipelines']:
                last_passed = get_pipeline_last_passed(pipeline['name'])
                pl_start = int(time.time()*1000)
                pl_end = 0
                if last_passed != None:
                    # Grab the instance for details
                    pipeline_url = "/go/api/pipelines/%s/instance/%s" % (pipeline['name'],last_passed)
                    run = requests.get(_url(pipeline_url), auth=('view','password'))
                    first_schedule = get_stages_first_schedule(run.json()['stages'])
                    for stage in run.json()['stages']:
                        (start,end,duration) = get_stage_ms_timing(pipeline['name'],run.json()['counter'],stage['name'],stage['counter'])
                        print("pl_stage_cycle_time,pipeline=%s,plctr=%d,stage=%s start=%d,end=%d,duration=%d" % (pipeline['name'],run.json()['counter'],stage['name'],start,end,duration))
                        if start < pl_start:
                            pl_start = start
                        if end > pl_end:
                            pl_end = end
                print("pl_cycle_time,pipeline=%s start=%d,end=%d,duration=%d" % (pipeline['name'],pl_start,pl_end,pl_end-pl_start))

                    # print run.json()
                # for stage in pipeline['stages']:
                #     print "\t\t",stage['name']
                #     # stage detais
                #     stage_url = "/go/api/stages/%s/%s/history" % (pipeline['name'],stage['name'])
                #     # stage_url = "/go/api/stages/%s/%s/instance/1/1" % (pipeline['name'],stage['name'])
                #     # GET /go/api/stages/:pipeline_name/:stage_name/history
                #     rstage = requests.get(_url(stage_url), auth=('view','password'))
                #     for stage_event in rstage.json():
                #         print "event ", stage_event

retrieve_gocd_metrics()
