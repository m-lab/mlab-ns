# mlab-ns Privacy Policy

## User-facing Disclaimer

**Context:** A link to this policy should be provided from wherever users are able to run a test which uses mlab-ns.

**Text:** This tool uses mlab-ns, M-Lab's name server. mlab-ns allows users' individual tests to be directed to the appropriate M-Lab server. Like any standard website, mlab-ns receives data over HTTP and collects minimal data for each request. This data is used to debug and improve mlab-ns. The data includes the client's IP address and it does not include location or other personally identifying information. The data is not released publicly. You can find the complete list of all the data collected by mlab-ns at http://mlab-ns.appspot.com/privacy.

## Data received and stored by mlab-ns

mlab-ns receives a number of data fields from each HTTP request. However, it does not store all of the fields received in the request. 

Like any other Google App Engine (GAE) instance, mlab-ns writes to two logs: an application log and a request log.

* The **application log** contains messages written by GAE itself about the application. Hosted applications may add additional content to this log if they wish. 
* The **request log** is automatically written by GAE when an HTTP request is received before handing it off to the application. Only GAE writes to the request log. The log is similar to the access log written by any HTTP server.

The sections below described what GAE writes to these two logs, focusing primarily on content that has implications on user privacy, along with additional operational information that mlab-ns additionally writes to the application log.

1. mlab-ns receives users' requests over HTTP.

  * Every HTTP request contains the fields listed here: [https://developers.google.com/appengine/docs/python/tools/webapp/requestclass](https://developers.google.com/appengine/docs/python/tools/webapp/requestclass)
  * Google App Engine also automatically adds to each incoming request the following fields, that describe the **end-user location**.
    * X-AppEngine-City
    * X-AppEngine-Region
    * X-AppEngine-Country
    * X-AppEngine-CityLatLong
  * mlab-ns also accepts additional user-defined arguments as part of the URL's query part, as described in the [mlab-ns design doc](DESIGN_DOC.md), all of which are optional, and listed below. User-defined arguments could be defined **by the end-user or by the M-Lab tool developer**.
    * policy
    * metro (Note: This is not metro area. See design doc.)
    * format
    * address family
    * country
    * city
    * latitude, longitude
      * Note that these location parameters (country, city, latitude, longitude) can be defined by M-Lab tool developers and can be arbitrary. They are useful when debugging queries to determine what mlab-ns would return for a user with this location.

2. When mlab-ns receives the above data, it collects some of those fields and computes other info based on them. In particular, mlab-ns:

  * Writes onto Google AppEngine **application log** the fields listed below.
    * tool_id
    * policy
    * response_format
    * geolocation_type
    * metro
    * time of the request (as set by time())
    * info about the user
      * info provided by the user or by the M-Lab tool (e.g., Neubot)
        * user_defined_ip
        * user_defined_address_family
      * info provided by GAE
        * ip_address_from_http_request
        * address_family_from_http_request
      * full user agent string
    * info about the server
      * slice_id
      * server_id
      * ipv4
      * ipv6
      * fqdn
      * site_id
      * city
      * country
      * latitude
      * longitude
    * mlab-ns also writes into GAE **application log** error messages and warnings. None of this additional content contains personal data about the users of M-Lab tools. 

  * GAE also automatically logs all the HTTP requests in the GAE request log.
    * These logs include user-defined location fields, since they are passed as arguments to the query.
    * It's NOT possible to disable this feature, nor to remove the query strings from these logs.
    * It is also possible to download the raw access logs from GAE using appcfg.py.

3. Upload full GAE **request log** onto **BigQuery tables**,  

  * to allow to easily query them 
  * to have fine-granularity access control. 
  * to support longevity of retention.

## Data destination ACL

  * Google AppEngine **application and request logs** are only accessible by admins of the Google app engine instance. These are not publicly available. Those who have access meet the definition below:
    * _Role:_ **mlab-ns GAE admin** include the Open Technology Institute staff responsible for overall M-Lab platform support and operation, and a few mlab-ns developers, as many as are necessary to help with debugging problems encountered in production.
    * _Responsibilities:_ Manage mlab-ns Google AppEngine application. Push new versions. Manage quota.

  * **BigQuery tables (with only request logs)** are accessible by any admin of the BigQuery project and by anybody explicitly allowed by the admin (via invite). Anybody can request an invite.
    * _Role:_ mlab-ns BigQuery admin
      * Note that the set of BigQuery admins is a subset of the GAE admins. 
    * _Responsibilities:_ Managing access to BigQuery. Manage BigQuery quota.
      * Access to these logs should rarely be needed and as such the admin can be less available. 

## Data retention
  
  * **Google app engine** logs are deleted according to the retention settings, defined by the mlab-ns GAE admin.
    * The default retention period is 365 days. The instance will be configured with a more conservative 120 days which still may seem like a long period but is acceptable given the access limitations and content limitations as described above.
    * Note that this retention period applies to **both the application logs and request logs.**
    * More info at [https://developers.google.com/appengine/docs/python/logservice/overview](https://developers.google.com/appengine/docs/python/logservice/overview)
  * BigQuery entries are kept forever, unless explicitly deleted by the admin.

## Debugging scenarios

  * Given an IP address X and a timestamp Y, it will be possible to tell which server mlab-ns returned for a request coming from X at Y.
  * Debugging (web-based) interface that allow users to send a request to mlab-ns and see which server it gets back and why (details from the mlab-ns decision process, without any PII info).

## Communication and policy aspects

The mlab-ns site should contain a page explaining the above: What is logged, and what the use of those logs are. The link to this page must be included with each measurement tool that uses mlab-ns, whether it's on the tool's site or in the application.
