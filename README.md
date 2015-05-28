# Deploying Code to mlab-ns

To deploy code updates to mlab-ns or to deploy mlab-ns to a fresh GCP test project, follow the instructions below.

## Testing environment
To deploy to the standard mlab-ns testing environment (mlab-nstesting.appspot.com), follow the instructions below with no modifications. To deploy to a different testing environment, you must edit server/app.yaml.testing to update the "application" field to your test environment's GCP project ID.

```
git clone https://code.google.com/p/m-lab.ns/ mlab-ns-testing
cd mlab-ns-testing
python environment_bootstrap.py testing
~/google_appengine/appcfg.py --oauth2 update server/
```

## Live environment

```
git clone https://code.google.com/p/m-lab.ns/ mlab-ns-live
cd mlab-ns-live
python environment_bootstrap.py live

# Verify all tests are passing
python server/unit_tests.py ~/google_appengine/ server/mlabns/tests/

# Deploy to production
~/google_appengine/appcfg.py --oauth2 update server/
```
# Bootstrapping a Fresh GCP Project

To deploy mlab-ns in a fresh GCP project, it is necessary to first deploy the code (see above). Once the code is deployed, mlab-ns needs seed data so that it can properly query Nagios and build up its datastore. To create this seed data, follow the instructions below.

Note: These instructions require billing to be enabled on your GCP project, as the data population process will exhaust a free-tiered project's daily AppEngine quota.

Note: These instructions require you to have `nagios.csv`, which is not under source control as it contains secret credentials, but is available to authorized users here: https://goo.gl/tfEg1v.

```
# Replace URL with other project's URL if not populating mlab-nstesting
GAE_URL = http://mlab-nstesting.appspot.com

appcfg.py --url ${GAE_URL}/_ah/remote_api upload_data \
  --config_file=server/bulkloader.yaml
  --filename=server/mlabns/conf/tools.csv \
  --kind=Tool

appcfg.py --url ${GAE_URL}/_ah/remote_api upload_data \
  --config_file=server/bulkloader.yaml \
  --filename=server/mlabns/conf/nagios.csv \
  --kind=Nagios
```

After the Datastore is populated with seed information, manually kick off the cron jobs to finish populating the Datastore with the latest live information from Nagios.

Run the following jobs from GCP under Compute > App Engine > Task queues > Cron Jobs.

1. /cron/check_site
1. /cron/check_ip
1. /cron/check_status

If bootstrapping was successful, you should see a populated map at the root mlab-ns URL (e.g. mlab-nstesting.appspot.com) with M-Lab's sites properly located.

## Gotchas

Help! After following the bootstrapping instructions, the map is not populated / my requests are being routed badly.

The likely cause is that the cron jobs did not complete successfully. Check the AppEngine logs to view the result of the cron jobs.

If the jobs failed due to "quota exceeded", you need to enable billing on the account.

If the jobs failed due to timeout exceeded or memory exhaustion, it's likely that you're hitting [issue #5](https://github.com/m-lab/mlab-ns/issues/5). The workaround for now is to keep running the cron jobs manually until they complete successfully. Each run is more likely to succeed because repeats of the job have to do successively fewer datastore/memcache inserts.
