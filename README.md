# Project-ServicePulse

**Production-oriented ServiceNow Data Engineering Platform on AWS**

ServicePulse is an end-to-end data engineering platform that ingests ServiceNow incident data through the ServiceNow REST API, processes it using a **Bronze → Silver → Gold** architecture, and delivers curated analytical data through **Amazon Redshift** for business intelligence and future machine-learning workloads.

The platform is designed around incremental processing, reliable orchestration, data quality, security, observability, and infrastructure automation.

> **Status:** 🚧 In Development

---

## Architecture

```text
                         ┌─────────────────────┐
                         │      ServiceNow     │
                         │      REST API       │
                         └──────────┬──────────┘
                                    │
                                    │ Incremental
                                    │ Extraction
                                    ▼
                         ┌─────────────────────┐
                         │   Amazon EventBridge│
                         │    Daily Schedule   │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   AWS Step Functions│
                         │     Orchestrator   │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │      AWS Lambda     │
                         │   API Ingestion     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────┐
                    │          S3 BRONZE          │
                    │                             │
                    │      Raw ServiceNow Data    │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                         ┌─────────────────────┐
                         │      AWS Glue       │
                         │      PySpark        │
                         │   Transformation    │
                         └──────────┬──────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────┐
                    │          S3 SILVER          │
                    │                             │
                    │   Cleaned / Validated       │
                    │        Parquet Data         │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                         ┌─────────────────────┐
                         │    Data Quality     │
                         │      Checks         │
                         └──────────┬──────────┘
                                    │
                                    ▼
                    ┌─────────────────────────────┐
                    │      Amazon Redshift        │
                    │                             │
                    │        GOLD / DWH           │
                    │       Star Schema           │
                    └──────────────┬──────────────┘
                                   │
                       ┌───────────┴───────────┐
                       │                       │
                       ▼                       ▼
                ┌──────────────┐       ┌──────────────┐
                │   Power BI   │       │ Future ML    │
                │  Analytics   │       │   Platform   │
                └──────────────┘       └──────────────┘
```

### Supporting AWS Services

```text
IAM              → Access control and least privilege
Secrets Manager  → ServiceNow credentials
CloudWatch       → Logs and monitoring
SNS              → Alerts and notifications
Glue Catalog     → Metadata and schema management
Terraform        → Infrastructure as Code
GitHub Actions   → CI/CD
```

---

## Why ServicePulse?

ServiceNow generates a continuous stream of operational ticket data. ServicePulse turns that operational data into a reliable analytical data platform.

The platform provides:

* Automated ServiceNow data ingestion
* Incremental processing
* Raw data preservation
* Distributed data transformation
* Data quality validation
* Analytical data warehousing
* Automated daily orchestration
* Operational monitoring
* BI-ready datasets
* ML-ready data assets

---

## Data Architecture

ServicePulse follows the **Medallion Architecture**.

```text
ServiceNow
    │
    ▼
┌─────────────┐
│   Bronze    │  Raw source data
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Silver    │  Cleaned & validated data
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    Gold     │  Business-ready warehouse
└──────┬──────┘
       │
       ├──────────► Power BI
       │
       └──────────► Future ML workloads
```

### Bronze

**Amazon S3**

Stores raw ServiceNow API responses with minimal transformation.

Primary goals:

* Preserve source data
* Auditability
* Replayability
* Historical retention

### Silver

**Amazon S3 + AWS Glue + PySpark**

Contains cleaned and standardized data stored in Parquet format.

Primary processing includes:

* Schema normalization
* Data type conversion
* Deduplication
* Null handling
* Timestamp standardization
* Data validation
* Derived attributes

### Gold

**Amazon Redshift**

Contains curated analytical datasets modeled using dimensional modeling principles.

The initial warehouse will include an incident fact table and supporting dimensions such as:

```text
fact_incident

dim_date
dim_user
dim_assignment_group
dim_priority
dim_category
dim_state
```

---

## Key Engineering Capabilities

### Incremental Ingestion

ServiceNow records are extracted using an incremental strategy based on fields such as:

```text
sys_updated_on
```

Only newly created or modified records are processed during each pipeline execution.

### Pagination

ServiceNow API responses are processed in bounded batches to avoid relying on a single long-running Lambda execution.

### Checkpointing

The pipeline maintains the last successfully processed extraction point.

```text
Last Successful Checkpoint
          │
          ▼
    ServiceNow API
          │
          ▼
New / Updated Records
```

### Idempotency

Repeated processing of the same source data should not create duplicate analytical records.

ServiceNow's `sys_id` provides a stable identifier for incident records.

### Data Quality

Validation is performed before data reaches the Gold warehouse.

Examples:

* Null checks
* Duplicate checks
* Schema validation
* Valid state/priority values
* Timestamp validation
* Referential integrity
* Business-rule validation

### Fault Tolerance

The workflow supports:

* Retries
* Failure states
* Checkpoint recovery
* Pipeline alerts
* Safe reprocessing

---

## Daily Pipeline

The target production workflow is:

```text
EventBridge
     │
     ▼
Step Functions
     │
     ▼
Retrieve Checkpoint
     │
     ▼
ServiceNow API
     │
     ▼
Lambda Ingestion
     │
     ▼
S3 Bronze
     │
     ▼
AWS Glue / PySpark
     │
     ▼
S3 Silver
     │
     ▼
Data Quality
     │
     ▼
Amazon Redshift
     │
     ▼
Power BI
```

The pipeline is intended to run automatically once per day.

---

## Technology Stack

| Category       | Technology                  |
| -------------- | --------------------------- |
| Source         | ServiceNow REST API         |
| Language       | Python                      |
| Processing     | PySpark                     |
| Data Lake      | Amazon S3                   |
| ETL            | AWS Glue                    |
| Metadata       | AWS Glue Data Catalog       |
| Ingestion      | AWS Lambda                  |
| Orchestration  | AWS Step Functions          |
| Scheduling     | Amazon EventBridge          |
| Data Warehouse | Amazon Redshift             |
| BI             | Power BI                    |
| Monitoring     | Amazon CloudWatch           |
| Alerting       | Amazon SNS                  |
| Secrets        | AWS Secrets Manager         |
| Security       | AWS IAM                     |
| Infrastructure | Terraform                   |
| Source Control | Git / GitHub                |
| CI/CD          | GitHub Actions              |
| Future ML      | AWS ML Services / SageMaker |

---

## Repository Structure

```text
servicepulse/
│
├── README.md
│
├── docs/
│   ├── architecture.md
│   ├── data-model.md
│   ├── ingestion.md
│   ├── data-quality.md
│   ├── orchestration.md
│   ├── security.md
│   ├── deployment.md
│   ├── monitoring.md
│   └── ml-roadmap.md
│
├── src/
│   ├── ingestion/
│   ├── common/
│   └── ...
│
├── glue/
│
├── sql/
│
├── terraform/
│
├── tests/
│
├── .github/
│   └── workflows/
│
├── requirements.txt
└── .gitignore
```

The repository structure will evolve as the implementation progresses.

---

## Current Implementation Status

| Component                  | Status     |
| -------------------------- | ---------- |
| Project architecture       | 🟢 Defined |
| Analytics Dashboard        | 🟢 Implemented |
| ServiceNow API integration | ⚪ Planned  |
| Incremental ingestion      | ⚪ Planned  |
| S3 Bronze                  | ⚪ Planned  |
| AWS Glue Silver            | ⚪ Planned  |
| Data Quality               | ⚪ Planned  |
| Redshift Gold              | ⚪ Planned  |
| Step Functions             | ⚪ Planned  |
| EventBridge                | ⚪ Planned  |
| CloudWatch                 | ⚪ Planned  |
| SNS alerts                 | ⚪ Planned  |
| Power BI                   | ⚪ Planned  |
| Terraform                  | ⚪ Planned  |
| CI/CD                      | ⚪ Planned  |
| Future ML platform         | 🔵 Future  |

> Status indicators will be updated as each component is implemented and tested.

---

## Documentation

Detailed engineering documentation will be maintained separately from this README.

| Document                                    | Description                                                     |
| ------------------------------------------- | --------------------------------------------------------------- |
| [`architecture.md`](docs/architecture.md)   | System architecture and design decisions                        |
| [`data-model.md`](docs/data-model.md)       | Silver schema and Redshift dimensional model                    |
| [`ingestion.md`](docs/ingestion.md)         | ServiceNow API, pagination, checkpoints and incremental loading |
| [`data-quality.md`](docs/data-quality.md)   | Data validation and quality rules                               |
| [`orchestration.md`](docs/orchestration.md) | Step Functions and EventBridge workflow                         |
| [`security.md`](docs/security.md)           | IAM, Secrets Manager and security controls                      |
| [`deployment.md`](docs/deployment.md)       | Terraform and deployment procedures                             |
| [`monitoring.md`](docs/monitoring.md)       | CloudWatch, logging and alerting                                |
| [`ml-roadmap.md`](docs/ml-roadmap.md)       | Future ML use cases and data requirements                       |

---

## Getting Started

> Detailed setup instructions will be added as the platform components are implemented.

### Prerequisites

Expected requirements include:

* AWS account
* ServiceNow instance with API access
* Python 3.x
* AWS CLI
* Terraform
* Git
* Power BI Desktop
* Appropriate AWS IAM permissions

### High-Level Setup

```text
1. Configure AWS environment
2. Configure ServiceNow API access
3. Store credentials in AWS Secrets Manager
4. Deploy infrastructure
5. Configure S3 data lake
6. Deploy Lambda ingestion
7. Configure Glue jobs
8. Configure Redshift
9. Deploy Step Functions workflow
10. Configure EventBridge schedule
11. Connect Power BI
```

Implementation-specific instructions will be documented in `docs/`.

---

## Analytics

The Gold warehouse is intended to support operational dashboards such as:

### Executive KPIs

* Total Tickets
* Open Tickets
* Resolved Tickets
* Current Backlog
* SLA Breach Rate
* Average Resolution Time
* Average Response Time

### Operational Analysis

* Tickets by priority
* Tickets by category
* Tickets by assignment group
* Tickets by state
* Ticket trends over time

### SLA Analysis

* SLA breaches by priority
* SLA breaches by assignment group
* Resolution time trends
* SLA compliance trends

---

## ServicePulse Analytics Dashboard

ServicePulse includes an interactive **Streamlit-based analytics dashboard** that provides real-time incident analytics powered by the Redshift data warehouse.

### Dashboard Features

**Real-Time KPIs**

* Total Incidents
* Open Incidents
* Critical Open Incidents (actionable metric)
* Average Incident Age
* On Hold Incidents

**Interactive Filters**

* Date Range
* Incident State
* Priority Level
* Category

All KPIs and charts react dynamically to filter changes.

**Analytics Charts**

* **Incident Trend** — Monthly incident creation trend line
* **Incident Status Distribution** — Pie chart showing incident state breakdown
* **Priority Distribution** — Horizontal bar chart by priority level
* **Category Distribution** — Horizontal bar chart by incident category
* **Incident Aging Analysis** — Bar chart with aging buckets (0-2, 3-7, 8-14, 15-30, 30+ days)

**Incident Details Table**

* Searchable and sortable incident data
* Key incident attributes (ID, description, state, priority, category, age, created date)
* Fully responsive to filter selection

### Technology Stack

* **Frontend Framework:** Streamlit
* **Data Visualization:** Plotly (interactive charts)
* **Data Processing:** Pandas
* **Database Connection:** AWS Redshift Data API
* **Authentication:** AWS Secrets Manager
* **Deployment:** Streamlit Cloud (or self-hosted)

### Architecture

```text
Amazon Redshift Data Warehouse
           │
           │ (Redshift Data API)
           │
           ▼
    Python / Pandas
           │
           ▼
    Streamlit Application
           │
           ├────────► Interactive Filters
           │
           ├────────► KPI Cards
           │
           ├────────► Plotly Charts
           │
           └────────► Incident Details Table
           │
           ▼
    User Browser
```

### Data Freshness

The dashboard shows:

* **Last Refresh Time** — When data was last queried from Redshift
* **Connection Status** — AWS Redshift connection indicator
* **Record Count** — Number of incidents in the current view

This demonstrates operational awareness of the data pipeline.

### Deployment

The dashboard can be deployed to:

* **Streamlit Cloud** — Free community deployment
* **Self-hosted** — Docker container on AWS ECS, EC2, or on-premises
* **AWS-native** — Integration with AWS services for enterprise deployments

---

## Future ML Platform

The curated Gold datasets are designed to support a separate downstream ML project.

### Planned Use Cases

**Ticket Classification**

```text
Ticket Description
       │
       ▼
NLP / ML Model
       │
       ▼
Category / Subcategory / Assignment Group
```

**SLA Breach Prediction**

```text
Ticket Features
       │
       ▼
ML Model
       │
       ▼
SLA Breach Probability
```

The ML platform will be developed independently after the Data Engineering platform is stable.

---

## Production Design Principles

ServicePulse is being designed around the following engineering principles:

* **Incremental over full-load processing**
* **Idempotent over duplicate-prone processing**
* **Automated over manual execution**
* **Observable over opaque pipelines**
* **Secure by default**
* **Infrastructure as Code**
* **Environment separation**
* **Testable components**
* **Recoverable workflows**
* **Documentation alongside implementation**

A feature will only be described as implemented once it has been built and tested.

---

## Roadmap

### Phase 1 — ServiceNow Ingestion

* [ ] ServiceNow API client
* [ ] Authentication
* [ ] Pagination
* [ ] Incremental extraction
* [ ] Checkpoint management
* [ ] Retry handling
* [ ] Bronze ingestion

### Phase 2 — Data Lake

* [ ] S3 Bronze
* [ ] S3 Silver
* [ ] Glue Catalog
* [ ] PySpark transformations
* [ ] Parquet partitioning

### Phase 3 — Data Quality

* [ ] Schema validation
* [ ] Completeness checks
* [ ] Duplicate detection
* [ ] Business rules
* [ ] Failure handling

### Phase 4 — Data Warehouse

* [ ] Redshift
* [ ] Star schema
* [ ] Fact tables
* [ ] Dimension tables
* [ ] Incremental loading

### Phase 5 — Orchestration

* [ ] Step Functions
* [ ] EventBridge
* [ ] Retry policies
* [ ] Failure states
* [ ] Checkpoint recovery

### Phase 6 — Analytics & Visualization

* [x] Redshift → Streamlit Dashboard
* [x] KPI Model
* [x] Operational Dashboard
* [x] Real-time Filtering
* [x] Interactive Charts (Plotly)
* [x] Data Freshness Indicators
* [ ] Redshift → Power BI
* [ ] SLA Dashboard

### Phase 7 — Productionization

* [ ] Terraform
* [ ] Dev/Prod environments
* [ ] GitHub Actions
* [ ] Automated tests
* [ ] Monitoring
* [ ] Alerting
* [ ] Operational runbook

### Phase 8 — Future ML Platform

* [ ] Ticket classification
* [ ] SLA breach prediction
* [ ] Feature engineering
* [ ] Model training
* [ ] Model evaluation
* [ ] Model deployment
* [ ] ML monitoring

---

## Project Status

**ServicePulse is currently in the architecture and implementation phase.**

The repository will be updated continuously as each component is implemented, tested, and productionized.

---

## License

License information will be added as the repository is finalized.

---

## Author

**Ravi Kumar**

Data Science · Machine Learning · Data Engineering · Generative AI

---

> **ServicePulse - Build the data foundation first. Turn operational data into reliable analytics and future ML capabilities.**
