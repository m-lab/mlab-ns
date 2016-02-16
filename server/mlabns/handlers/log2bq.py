# TODO(claudiu) Update this with the latest online version
# http://code.google.com/p/log2bq/.
import StringIO
import csv
import httplib2
import json
import logging
import os
import time
import webapp2

from google.appengine.api import files
from google.appengine.api import logservice
from google.appengine.ext.webapp import template

from apiclient.discovery import build
from oauth2client.appengine import AppAssertionCredentials

from mapreduce import base_handler, mapreduce_pipeline
from mapreduce.lib import pipeline

from mlabns import util

import config

credentials = AppAssertionCredentials(
    scope='https://www.googleapis.com/auth/bigquery')

http = credentials.authorize(http=httplib2.Http())
service = build('bigquery', 'v2', http=http)


class Log2Bq(base_handler.PipelineBase):
    """A pipeline to ingest log as CSV in Google Big Query."""

    def run(self, start_time, end_time, version_ids):
        files = yield Log2Gs(start_time, end_time, version_ids)
        yield Gs2Bq(files)


class Log2Gs(base_handler.PipelineBase):
    """A pipeline to ingest log as CSV in Google Storage."""

    def run(self, start_time, end_time, version_ids):
        # Create a MapperPipeline w/ `LogInputReader`, `FileOutputWriter`
        yield mapreduce_pipeline.MapperPipeline(
            "log2bq",
            "mlabns.handlers.log2bq.log2csv",
            "mapreduce.input_readers.LogInputReader",
            "mapreduce.output_writers.FileOutputWriter",
            params={
                "input_reader": {
                    "start_time": start_time,
                    "end_time": end_time,
                    "minimum_log_level": logservice.LOG_LEVEL_INFO,
                    "version_ids": version_ids,
                },
                "output_writer": {
                    "filesystem": "gs",
                    "gs_bucket_name": config.gs_bucket_name,
                }
            },
            shards=16)


# Create a mapper function that converts request logs object to CSV.
def log2csv(request_log):
    """Convert log API RequestLog object to csv."""

    row = None
    for app_log in request_log.app_logs:
        words = app_log.message.split(',')
        if words[0] == '[lookup]':
            row = app_log.message.split(',')[1:]
            row.append(str(request_log.latency))
            row.append(request_log.user_agent)
            break

    if row is not None:
        s = StringIO.StringIO()
        w = csv.writer(s)
        w.writerow(row)
        line = s.getvalue()
        s.close()
        yield line


# Create a pipeline that takes gs:// files as argument and ingest them
# using a Big Query `load` job.
class Gs2Bq(base_handler.PipelineBase):
    """A pipeline to ingest log csv from Google Storage to Google BigQuery."""

    def run(self, files):
        jobs = service.jobs()
        gs_paths = [f.replace('/gs/', 'gs://') for f in files]
        result = service.jobs().insert(
            projectId=config.project_id,
            body={
                'projectId': config.project_id,
                'configuration': {
                    'load': {
                        'sourceUris': gs_paths,
                        'schema': {
                            'fields': config.bigquery_schema,
                        },
                        'destinationTable': {
                            'projectId': config.project_id,
                            'datasetId': config.bigquery_dataset_id,
                            'tableId': config.bigquery_table_id
                        },
                        'createDisposition': 'CREATE_IF_NEEDED',
                        'writeDisposition': 'WRITE_APPEND',
                        'encoding': 'UTF-8'
                    }
                }
            }).execute()
        yield BqCheck(result['jobReference']['jobId'])


# Create a pipeline that check for a Big Query job status
class BqCheck(base_handler.PipelineBase):
    """A pipeline to check for Big Query job status."""

    def run(self, job):
        jobs = service.jobs()
        status = jobs.get(projectId=config.project_id, jobId=job).execute()
        job_state = status['status']['state']
        if job_state == 'PENDING' or job_state == 'RUNNING':
            delay = yield pipeline.common.Delay(seconds=1)
            with pipeline.After(delay):
                yield BqCheck(job)
        else:
            yield pipeline.common.Return(status)


# Create an handler that launch the pipeline and redirect to the
# pipeline UI.
class Log2BigQueryHandler(webapp2.RequestHandler):

    def get(self):
        now = time.time()
        start_time = now - 60 * 15
        major, minor = os.environ["CURRENT_VERSION_ID"].split(".")
        p = Log2Bq(start_time, now, [major])
        p.start()
        #self.redirect('/mapreduce/pipeline/status?root=%s' % p.root_pipeline_id)
