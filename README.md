[![Build
Status](https://travis-ci.org/m-lab/mlab-ns.svg?branch=master)](https://travis-ci.org/m-lab/mlab-ns)
[![Coverage
Status](https://coveralls.io/repos/m-lab/mlab-ns/badge.svg?branch=master&service=github)](https://coveralls.io/github/m-lab/mlab-ns?branch=master)

# Deploying Code to mlab-ns

mlab-ns is intergrated with Travis to build and deploy to testing and production.

* commits to master are built and pushed to mlab-ns-testing by travis
* tagged releases are built and pushed to mlab-ns production by travis

## Manual Deployments

Though we use Travis now to build and deploy, the previous instructions are
retained below for reference.

### Testing environment

To deploy to the standard mlab-ns testing environment
(locate-dot-mlab-sandbox.appspot.com), follow the instructions below with no
modifications. To deploy to a different testing environment, you may need to
edit `server/app.yaml.mlab-sandbox` to update the "service" field to work
within your test environment's other App Engine services names.

```
git clone --recursive https://github.com/m-lab/mlab-ns.git mlabns-testing
cd mlabns-testing

# Or, for an existing repo:
# git checkout master
# git submodule update --init
# git pull origin master

python environment_bootstrap.py testing
~/google_appengine/appcfg.py --oauth2 update server/
```

### Live environment

```
git clone --recursive https://github.com/m-lab/mlab-ns.git mlabns-live
cd mlabns-live

# Or, for an existing repo:
# git checkout master
# git submodule update --init
# git pull origin master

python environment_bootstrap.py live

# Verify all tests are passing
./build

# Deploy to production
~/google_appengine/appcfg.py --oauth2 update server/
```

When deploying to production make sure to deploy from the master branch.

## Bootstrapping a Fresh GCP Project

To deploy mlab-ns in a fresh GCP project, it is necessary to first deploy the
code (see above). Once the code is deployed, mlab-ns needs seed data so that it
can properly query Prometheus and build up its datastore. To create this seed
data, follow the instructions below.

Note: These instructions require billing to be enabled on your GCP project, as
the data population process will exhaust a free-tiered project's daily
AppEngine quota.

Note: These instructions require you to have files named `nagios.csv` and
`prometheus.csv`, which are not under source control as they contains secret
credentials, but is available to authorized users here: https://goo.gl/tfEg1v.
Manually create those two files and paste the file content found at that URL
into the files before running the `appcfg.py` commands below.

```
# Replace URL with other project's URL if not populating mlab-sandbox.
GAE_URL=http://locate-dot-mlab-sandbox.appspot.com
TOKEN=$( gcloud auth print-access-token )

appcfg.py --url ${GAE_URL}/_ah/remote_api upload_data \
  --oauth2_access_token=${TOKEN} \
  --config_file=server/bulkloader.yaml \
  --filename=server/mlabns/conf/tools.csv \
  --kind=Tool

appcfg.py --url ${GAE_URL}/_ah/remote_api upload_data \
  --oauth2_access_token=${TOKEN} \
  --config_file=server/bulkloader.yaml \
  --filename=server/mlabns/conf/nagios.csv \
  --kind=Nagios

appcfg.py --url ${GAE_URL}/_ah/remote_api upload_data \
  --oauth2_access_token=${TOKEN} \
  --config_file=server/bulkloader.yaml \
  --filename=server/mlabns/conf/prometheus.csv \
  --kind=Prometheus

appcfg.py --url ${GAE_URL}/_ah/remote_api upload_data \
  --oauth2_access_token=${TOKEN} \
  --config_file=server/bulkloader.yaml \
  --filename=server/mlabns/conf/redirect_probability.csv \
  --kind=RedirectProbability
```

Note: If you see repeated errors including `Refreshing due to a 401 (attempt
1/2)`, this is an [appcfg
bug](https://code.google.com/p/googleappengine/issues/detail?id=12435). To work
around the issue, delete any cached appcfg tokens in your home directory (will
likely start with `~/.appcfg*`).

After the Datastore is populated with seed information, manually kick off the
cron jobs to finish populating the Datastore with the latest live information
from Nagios.

Run the following jobs from GCP under Compute > App Engine > Task queues > Cron Jobs.

1. `/cron/check_site`
1. `/cron/check_status`

If bootstrapping was successful, you should see a populated map at the root
mlab-ns URL (e.g. mlab-nstesting.appspot.com) with M-Lab's sites properly
located.

## Gotchas

Help! After following the bootstrapping instructions, the map is not populated
/ my requests are being routed badly.

The likely cause is that the cron jobs did not complete successfully. Check the
AppEngine logs to view the result of the cron jobs.

If the jobs failed due to "quota exceeded", you need to enable billing on the
account.

If the jobs failed due to timeout exceeded or memory exhaustion, it's likely
that you're hitting [issue #5](https://github.com/m-lab/mlab-ns/issues/5). The
workaround for now is to keep running the cron jobs manually until they
complete successfully. Each run is more likely to succeed because repeats of
the job have to do successively fewer datastore/memcache inserts.
