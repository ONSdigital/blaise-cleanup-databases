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
| `DATABASE_IP_ADDRESS` | Private IP address of the Cloud SQL instance |
| `DATABASE_PORT` | MySQL port on the Cloud SQL instance (usually `3306`) |
| `DATABASE_USER` | MySQL database user |
| `DATABASE_PASSWORD` | MySQL password, exposed to the function from Secret Manager |

The function connects directly to the Cloud SQL private IP using MySQL password
authentication. Configure `DATABASE_PASSWORD` as a Secret Manager-backed
environment variable and grant the function's service account access to that
secret. The function must also have VPC network access and firewall connectivity
to the Cloud SQL instance on the configured port.

An empty questionnaire GUID list stops cleanup to avoid deleting all old
questionnaire records. The function deletes `CMA_Launcher_Form` and
`CMA_Attempts_Form` rows only when `TimeCreated` is older than the configured
threshold and `MainSurveyId` is not installed; NULL IDs are treated as absent.
It deletes `CMA_Logging_Form` rows only when both `TimeCreated` and
`LastModification` are older than the threshold; NULL `LastModification` values are
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

```shell
gcloud auth login
gcloud config set project ons-blaise-v2-dev
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
SERVER_PARK=gusty
DATABASE_IP_ADDRESS='10.0.0.5'
DATABASE_PORT='3306'
DATABASE_USER='blaise'
DATABASE_PASSWORD='configure-from-secret-manager'
CMA_TIME_THRESHOLD='90'
```
