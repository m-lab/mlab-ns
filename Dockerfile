FROM google/cloud-sdk

ENV PYTHONPATH $PYTHONPATH:/usr/lib/google-cloud-sdk/platform/google_appengine
# NOTE: the Cloud SDK component manager is disabled in this install, so
# `gcloud components install app-engine-python` does not work. So, use:
RUN apt-get update
RUN apt-get install -y google-cloud-sdk-app-engine-python
COPY test_requirements.txt /
RUN pip install -r /test_requirements.txt
RUN pip install coveralls
RUN pip install django==1.2 jinja2==2.6
COPY . /workspace
