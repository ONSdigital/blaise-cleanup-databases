# blaise-cleanup-databases
Cloud functions to support cleaning of databases

## CMA cleanup

Deploy `main.cma_database_cleanup` as an HTTP Cloud Function and invoke it with
an authenticated POST request (for example, from Cloud Scheduler). The request
body is ignored. Configure the following environment variables:

| Variable | Purpose |
| --- | --- |
| `QUESTIONNAIRES_URL` | GET endpoint returning installed server-park questionnaires |
| `QUESTIONNAIRES_BEARER_TOKEN` | Optional bearer token for that endpoint; supply securely |
| `DATABASE_USER`, `DATABASE_PASSWORD` | MySQL credentials; supply securely |
| `DATABASE_SOCKET` | Cloud SQL Unix socket path, if using a Cloud SQL connection |
| `DATABASE_HOST`, `DATABASE_PORT` | TCP connection settings (default `localhost:3306`) |

The questionnaire endpoint must return either a JSON array of names or
`{"questionnaires": ["SurveyA", "SurveyB"]}`. Objects with a `name` field in the
array are also accepted. Confirm this contract and that `MainSurveyId` corresponds
to the returned names under the database collation before deploying. An empty or invalid response stops
the entire cleanup without deleting any records.

The function deletes rows in `blaise.CMA_Logging_Form` where `TimeCreated` is
strictly older than 90 days. For `CMA_Launcher_Form` and `CMA_Attempts_Form`, it
also requires `MainSurveyId` to be absent from the installed questionnaire
names; NULL identifiers are retained. All three deletes run in one transaction.
The cutoff and MySQL session use UTC: verify that `TimeCreated` stores UTC values
before running this against production. The function logs deleted row counts.

After dependency registry access is available, regenerate `poetry.lock` with
`poetry lock`, install dependencies with `poetry install`, and run
`poetry run python -m pytest`. The new MySQL driver could not be resolved in the
current offline environment, so the lock file is not yet in sync.
