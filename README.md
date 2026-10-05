# blaise-cleanup-databases
Cloud functions to support cleaning of databases

## CMA cleanup

Deploy `main.cma_database_cleanup` as an HTTP Cloud Function and invoke it with
an authenticated POST request (for example, from Cloud Scheduler). The request
body is ignored. Configure the following environment variables:

| Variable | Purpose |
| --- | --- |
| `BLAISE_API_URL` | Blaise REST API host used by `blaise-restapi` |
| `SERVER_PARK` | Blaise server park queried for installed questionnaire GUIDs |
| `CMA_TIME_THRESHOLD` | Positive retention period in days |
| `PROJECT_ID` | Google Cloud project containing the Cloud SQL instance |
| `SQL_REGION` | Cloud SQL instance region |
| `SQL_INSTANCE_NAME` | Cloud SQL instance ID |
| `DATABASE_USER` | Cloud SQL IAM database user for the function's service account |
| `SQL_IP_TYPE` | Optional connector IP type (`public`, `private`, or `psc`); defaults to `public` |

The function uses Application Default Credentials through the Cloud SQL Python
Connector with automatic IAM database authentication. Do not configure a database
password. Enable the Cloud SQL Admin API, enable IAM database authentication on
the instance, create the IAM database user, and grant the function's service
account the Cloud SQL Client and Cloud SQL Instance User roles. For MySQL IAM
service-account users, `DATABASE_USER` is the service account name without
`@project-id.iam.gserviceaccount.com`. Private IP or PSC also requires the
function to have network access to that instance.

An empty questionnaire GUID list stops cleanup to avoid deleting all old
questionnaire records. The function deletes `CMA_Launcher_Form` and
`CMA_Attempts_Form` rows only when `TimeCreated` is older than the configured
threshold and `MainSurveyId` is not installed; NULL IDs are treated as absent.
It deletes `CMA_Logging_Form` rows only when both `TimeCreated` and
`LastModified` are older than the threshold; NULL `LastModified` values are
treated as not recently modified. The cutoff and MySQL session use UTC. All three
deletes run in one transaction, and the function logs deleted row counts.

## Local Development

### Clone and install packages

```shell
git clone https://github.com/ONSdigital/blaise-cleanup-databases.git
cd blaise-cleanup-databases
poetry install
```

### Authenticate with Google Cloud (keyless)

Use service account impersonation to auth with BIMS and BUS.

```shell
gcloud auth login
gcloud config set project ons-blaise-v2-dev
gcloud auth application-default login --impersonate-service-account=ons-blaise-v2-dev@appspot.gserviceaccount.com
```

### Start an IAP tunnel to Blaise REST API

Run this in a separate terminal and keep it running:

```shell
gcloud compute start-iap-tunnel restapi-1 80 --local-host-port=localhost:8080 --zone europe-west2-a
```

Expected output includes `Listening on port [8080]`.

### Configure environment variables

Create a `.env` file in the repository root. You can find IAP client IDs from an existing deployment:

- App Engine -> Versions -> `dqs-ui` -> View Config

Example `.env` file:

```ini
BLAISE_API_URL=localhost:8080
PROJECT_ID=ons-blaise-v2-dev-sandbox123
SERVER_PARK=gusty
SQL_INSTANCE_NAME='blaise-dev-ef8bfb2b'
SQL_REGION='europe-west2'
DATABASE_USER='ons-blaise-v2-dev'
CMA_TIME_THRESHOLD='90'
```
