# Bootstrapping a Fresh GCP Project

To deploy mlab-ns in a fresh GCP project, it is necessary to first bootstrap the Datastore with necessary initial data. `nagios.csv` is a file containing secret credentials, and so is under access control here: https://goo.gl/tfEg1v.

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

# Deploying Updated Code to mlab-ns

## Testing environment

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
