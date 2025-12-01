# FDS v2 — Fraud Detection System Prototype
A Python-based reimplementation of real fraud-detection workflows.

---

## 1. Overview

FDS v2 is a backend prototype that reconstructs fraud-detection workflows I previously operated in real fintech environments.  
The system focuses on clean domain modelling, fault-tolerant ingestion, and asynchronous rule evaluation, using Django, Celery, Redis, PostgreSQL, and the Outbox pattern.

The goal is to demonstrate how risk systems can remain predictable, reliable, and traceable under high event volume.

---

## 2. Problem Statement

Modern payment platforms continuously receive:

- Orders  
- Payment attempts  
- Device and account signals  
- Behavioral patterns (velocity, mismatch, anomalies)

A fraud system must:

- ingest events safely  
- avoid blocking upstream services  
- evaluate rules efficiently  
- prevent duplicated detection  
- maintain a complete audit trail  

FDS v2 reproduces this pipeline with production-ready architectural choices.

---

## 3. Architecture

### 3.1 Data & Control Flow

```
---------------------------------------
client_server
    │
    │ HTTP POST /orders
    ▼
Django API (fds_api + fds_django)
    │
    ├─ Save Order (upsert)
    └─ Insert Outbox(READY)
---------------------------------------
                 │
                 ▼
---------------------------------------
Outbox Table (DB)
    │  
    ▼
Dispatcher Task (dispatch_outbox_batch)
    │
    └─ detect_case_task.delay(payload)
---------------------------------------
                 │
                 ▼
---------------------------------------
Celery Worker Pool
    │
    ├─ Idempotency guard (Processed)
    ├─ detect_case(db, CaseParams)
    ├─ Apply blocklist (transactional)
    └─ Insert Processed
---------------------------------------
```

### 3.2 Key Principles

- Ingestion vs evaluation separation  
- Idempotent ingestion  
- Outbox as source of truth  
- Asynchronous worker evaluation  
- Clean domain modelling  

---

## 4. Domain Model

| Entity        | Description |
|---------------|-------------|
| Order         | User-intent event with items, price, metadata |
| Purchase      | Payment attempt tied to an order |
| Outbox        | Durable event queue for async processing |
| Rule Engine   | Stateless evaluator of SQL-style rules |
| Blocklist     | Stores account/device/card restrictions |

### Why this domain?

Fraud systems receive heterogeneous payloads from multiple upstream services.  
Separating Order, Purchase, and Outbox ingestion keeps the system consistent, observable, and easy to reason about.

---

## 5. Core Components

### 5.1 Ingestion API 

- Validates event snapshots  
- Idempotent upsert  
- Writes Outbox event in READY state  
- No heavy detection logic in request/response  

### 5.2 Outbox Pattern

A persistent, auditable event log ensuring durability, replayability, and crash-safe dispatch.  
This solves real production issues such as lost events, duplicated detection, and inconsistent state.

### 5.3 Celery Worker

- Reads READY events  
- Runs rule evaluation  
- Applies blocklist side effects  
- Writes Processed records for idempotency  

### 5.4 Rule Engine

- Stateless logic  
- SQL-like rule conditions  
- Cached rules for performance  
- Evaluates conditions: high-risk country, new devices, velocity rules, blocklist checks  

### 5.5 Containerized Runtime

- Django API  
- Celery workers  
- Redis broker  

Docker provides a reproducible local environment.

---

## 6. Architectural Rationale

### 6.1 Separate Core Logic from Django

- Clear domain boundaries  
- Easier testing  
- Framework-agnostic  
- Future-proof for microservices or queue consumers  

### 6.2 SQL-Based Rules

- Analysts think in SQL  
- Rules change frequently  
- No redeployment required  
- Highly expressive condition syntax  

### 6.3 Asynchronous Detection

- Heavy rule evaluation does not affect API latency  
- Scales horizontally  
- Decouples ingestion throughput from evaluation workload  

### 6.4 Outbox Guarantees

Prevents:

- Lost events between DB commit and dispatch  
- Duplicate detection  
- Inconsistent or partial state  

Outbox makes ingestion atomic and traceable.

---

## 7. Example Scenario

A user in Japan attempts a high-value payment from an unseen device:

1. `/ingest/purchase` received  
2. Snapshot saved and Outbox event created  
3. Worker consumes event  
4. Rule engine loads context: new device, unusual amount, account mismatch  
5. Rules trigger   
   - “High-value + unknown device → REVIEW”
   - “High-value + risk_country=BR → BLOCK”
   - “3+ payment attempts in 10 minutes → BLOCK”
6. Blocklist may be updated  
7. Decision saved for audit  

This illustrates the end-to-end detection pipeline.

---

## 8. Why This Architecture Works

- Scalable: worker pools scale horizontally  
- Reliable: Outbox guarantees event durability  
- Traceable: every snapshot preserved for investigation  
- Clean: well-defined domain boundaries  
- Extensible: easy to add rules or event types  

---

## 9. Future Extensions

- **Rule Management UI**  
  Lets analysts update rules, thresholds, and conditions without code changes.  
  Directly connected to the SQL-based rule storage.


- **Rule Simulation & Replay Engine**  
  Replays historical snapshots to check how rule changes behave before deployment.  
  Ensures predictable detection behavior.


- **Event Reprocessing Pipeline**  
  Re-runs past events whenever rules or blocklists change.  
  Keeps the system consistent as risk logic evolves.


- **Fine-Grained Audit Viewer**  
  Shows each detection step: inputs, triggered rules, intermediate states, and final decisions.  
  Makes investigation and explanation straightforward.


- **Chargeback & Dispute Analytics Dashboard**  
  Aggregates outcomes, rule triggers, false-positive rates, and dispute ratios.  
  Helps evaluate rule effectiveness and blocklist impact.

---

## 10. Tech Stack

- Python 3.11  
- Django / DRF
- Celery  
- Redis  
- PostgreSQL  
- Docker  

