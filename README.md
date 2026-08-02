# WordPress to PostgreSQL ETL Data Pipeline

A production-grade Python ETL pipeline engineered to extract student profile records from heterogeneous sources (WordPress MySQL, Google Drive APIs, and flat Excel files), transform and normalize the schema, and load them into PostgreSQL.

---

## Architecture Overview

```mermaid
flowchart TD
    classDef source fill:#e1f5fe,stroke:#0288d1,stroke-width:2px,color:#01579b;
    classDef extract fill:#fff3e0,stroke:#f57c00,stroke-width:2px,color:#e65100;
    classDef transform fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#4a148c;
    classDef load fill:#e8f5e9,stroke:#388e3c,stroke-width:2px,color:#1b5e20;
    classDef storage fill:#eceff1,stroke:#455a64,stroke-width:2px,color:#263238;

    subgraph SOURCE["1. SOURCE LAYER (Heterogeneous Ingestion)"]
        direction TB
        S1[("WordPress DB\n(MySQL / MariaDB)\nwp_users & wp_usermeta")]:::source
        S2["Cloud Storage / Web\n(Google Drive API / REST)"]:::source
        S3["Flat File Storage\n(Local / Remote .xlsx)"]:::source
    end

    subgraph ENGINE["2. EXTRACTION & ETL RUNTIME (Python Engine)"]
        direction TB
        
        subgraph CONN["Driver & Network Layer"]
            C1["PyMySQL Driver\n(Port 3306 / SSH Tunnel)"]:::extract
            C2["Google OAuth 2.0 / HTTP\n(gspread / Requests)"]:::extract
            C3["OpenPyXL / IO Stream\n(Disk / Byte Stream)"]:::extract
        end

        subgraph TRANSFORM["Transformation & Normalization"]
            T1["SQL Pivot / Relational Join\n(Extract Meta Keys to Schema Columns)"]:::transform
            T2["Vectorized Pandas DataFrame\n(In-Memory Type Casting & Cleanup)"]:::transform
            T3["Schema Enforcement & Validation\n(Null Handling, Date Normalization)"]:::transform
        end

        subgraph LOAD_MGT["Load & Transaction Management"]
            L1["SQLAlchemy ORM Connection Pool\n(Unified Connection Management)"]:::load
            L2["Psycopg2 Driver\n(PostgreSQL Wire Protocol)"]:::load
        end

        C1 --> T1
        C2 --> T2
        C3 --> T2
        T1 --> T2
        T2 --> T3
        T3 --> L1
        L1 --> L2
    end

    subgraph TARGET["3. TARGET PERSISTENCE LAYER (PostgreSQL)"]
        direction TB
        PG[("PostgreSQL Database Engine\nDb: SchoolDatabase")]:::storage
        SCH["Schema: SchoolRegistration\nTable: Students"]:::storage
        PG --- SCH
    end

    S1 ==> C1
    S2 ==> C2
    S3 ==> C3
    L2 ==>|"Batch INSERT / Transaction Commit"| SCH

    style SOURCE fill:#ffffff,stroke:#90caf9,stroke-width:2px,stroke-dasharray: 5 5;
    style ENGINE fill:#ffffff,stroke:#ffcc80,stroke-width:2px,stroke-dasharray: 5 5;
    style TARGET fill:#ffffff,stroke:#a5d6a7,stroke-width:2px,stroke-dasharray: 5 5;


## Repository Layout

```text
SchoolPipeProject/
├── .env.example                      # Template for DB passwords & API keys (NO real secrets)
├── .gitignore                        # Prevents logs, secrets, and cache from committing
├── README.md                         # Architecture overview and documentation
├── requirements.txt                  # Python dependencies (pandas, sqlalchemy, etc.)
│
├── config/                           # Environment & application settings
│   ├── __init__.py
│   └── settings.py                   # Environment variable loader
│
├── data/                             # Local staging folder (ignored by Git)
│   ├── input/                        # Incoming Excel / flat files
│   └── logs/                         # Pipeline execution logs
│
├── src/                              # ETL pipeline source code
│   ├── __init__.py
│   ├── main.py                       # Main pipeline orchestration entry point
│   │
│   ├── extractors/                   # Data ingestion modules
│   │   ├── __init__.py
│   │   ├── wordpress_extractor.py    # MySQL connector (wp_users & wp_usermeta)
│   │   ├── gdrive_extractor.py       # Google Drive API connector
│   │   └── excel_extractor.py        # Local Excel file parser
│   │
│   ├── transformers/                 # Data transformation & normalization
│   │   ├── __init__.py
│   │   ├── metadata_pivoter.py      # Pivots wp_usermeta key-values into relational rows
│   │   └── schema_sanitizer.py      # Pandas vectorization, null checks, date parsing
│   │
│   └── loaders/                      # Data persistence
│       ├── __init__.py
│       └── postgres_loader.py       # SQLAlchemy connection pool & PostgreSQL batch load
│
└── tests/                            # Automated test suite
    ├── test_extractors.py
    └── test_transformers.py