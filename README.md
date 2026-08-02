\# WordPress to PostgreSQL ETL Data Pipeline



A production-grade Python ETL pipeline engineered to extract student profile records from heterogeneous sources (WordPress MySQL, Google Drive APIs, and flat Excel files), transform and normalize the schema, and load them into PostgreSQL.



\---



\## Architecture Overview



```mermaid

flowchart TD

&#x20;   classDef source fill:#e1f5fe,stroke:#0288d1,stroke-width:2px,color:#01579b;

&#x20;   classDef extract fill:#fff3e0,stroke:#f57c00,stroke-width:2px,color:#e65100;

&#x20;   classDef transform fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#4a148c;

&#x20;   classDef load fill:#e8f5e9,stroke:#388e3c,stroke-width:2px,color:#1b5e20;

&#x20;   classDef storage fill:#eceff1,stroke:#455a64,stroke-width:2px,color:#263238;



&#x20;   subgraph SOURCE\["1. SOURCE LAYER (Heterogeneous Ingestion)"]

&#x20;       direction TB

&#x20;       S1\[("WordPress DB\\n(MySQL / MariaDB)\\nwp\_users \& wp\_usermeta")]:::source

&#x20;       S2\["Cloud Storage / Web\\n(Google Drive API / REST)"]:::source

&#x20;       S3\["Flat File Storage\\n(Local / Remote .xlsx)"]:::source

&#x20;   end



&#x20;   subgraph ENGINE\["2. EXTRACTION \& ETL RUNTIME (Python Engine)"]

&#x20;       direction TB

&#x20;       

&#x20;       subgraph CONN\["Driver \& Network Layer"]

&#x20;           C1\["PyMySQL Driver\\n(Port 3306 / SSH Tunnel)"]:::extract

&#x20;           C2\["Google OAuth 2.0 / HTTP\\n(gspread / Requests)"]:::extract

&#x20;           C3\["OpenPyXL / IO Stream\\n(Disk / Byte Stream)"]:::extract

&#x20;       end



&#x20;       subgraph TRANSFORM\["Transformation \& Normalization"]

&#x20;           T1\["SQL Pivot / Relational Join\\n(Extract Meta Keys to Schema Columns)"]:::transform

&#x20;           T2\["Vectorized Pandas DataFrame\\n(In-Memory Type Casting \& Cleanup)"]:::transform

&#x20;           T3\["Schema Enforcement \& Validation\\n(Null Handling, Date Normalization)"]:::transform

&#x20;       end



&#x20;       subgraph LOAD\_MGT\["Load \& Transaction Management"]

&#x20;           L1\["SQLAlchemy ORM Connection Pool\\n(Unified Connection Management)"]:::load

&#x20;           L2\["Psycopg2 Driver\\n(PostgreSQL Wire Protocol)"]:::load

&#x20;       end



&#x20;       C1 --> T1

&#x20;       C2 --> T2

&#x20;       C3 --> T2

&#x20;       T1 --> T2

&#x20;       T2 --> T3

&#x20;       T3 --> L1

&#x20;       L1 --> L2

&#x20;   end



&#x20;   subgraph TARGET\["3. TARGET PERSISTENCE LAYER (PostgreSQL)"]

&#x20;       direction TB

&#x20;       PG\[("PostgreSQL Database Engine\\nDb: SchoolDatabase")]:::storage

&#x20;       SCH\["Schema: SchoolRegistration\\nTable: Students"]:::storage

&#x20;       PG --- SCH

&#x20;   end



&#x20;   S1 ==> C1

&#x20;   S2 ==> C2

&#x20;   S3 ==> C3

&#x20;   L2 ==>|"Batch INSERT / Transaction Commit"| SCH



&#x20;   style SOURCE fill:#ffffff,stroke:#90caf9,stroke-width:2px,stroke-dasharray: 5 5;

&#x20;   style ENGINE fill:#ffffff,stroke:#ffcc80,stroke-width:2px,stroke-dasharray: 5 5;

&#x20;   style TARGET fill:#ffffff,stroke:#a5d6a7,stroke-width:2px,stroke-dasharray: 5 5;

```



\---



\## Key Features



\* \*\*Schema Transformation:\*\* Pivots WordPress key-value pair metadata (`wp\_usermeta`) into flat relational columns (`first\_name`, `last\_name`, `phone`).

\* \*\*In-Memory Operations:\*\* Leverages `pandas` vectorization to sanitize data, format dates, and handle nulls without writing intermediate files to disk.

\* \*\*Database Abstraction:\*\* Uses `SQLAlchemy` and `psycopg2` for connection pooling, explicit schema handling (`"SchoolRegistration"."Students"`), and atomic transaction handling.



\---



\## Setup \& Installation



1\. \*\*Clone the repository:\*\*

&#x20;  ```bash

&#x20;  git clone \[https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)

&#x20;  cd your-repo-name

&#x20;  ```



2\. \*\*Install required dependencies:\*\*

&#x20;  ```bash

&#x20;  pip install pandas sqlalchemy pymysql psycopg2-binary openpyxl

&#x20;  ```



3\. \*\*Configure connection strings \& run:\*\*

&#x20;  Update database credentials in the configuration section and execute:

&#x20;  ```bash

&#x20;  python wp\_to\_postgres.py

&#x20;  ```

