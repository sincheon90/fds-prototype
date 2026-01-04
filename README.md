# FDS v2 — Fraud Detection System Prototype
A Python-based reimplementation of real fraud-detection workflows.

Decision-focused redesign for observability, replayability, and auditability.


---

## 0. Overview

FDS v2 is a backend prototype that reconstructs fraud-detection workflows I previously operated in real fintech environments.

This project emphasizes predictable behavior, explicit decisions, and operational traceability under realistic constraints.

The system is designed to show not only how fraud detection can be implemented,
but how architectural decisions shape observability, explainability, and long-term operability.


---

## 1. Why This Project Exists

This project exists as a deliberate effort to re-engage with fraud detection from a system-design perspective. 

I had previously operated production FDS pipelines,
but over time, many architectural decisions became implicit - shaped by legacy constraints, operational trade-offs, and incremental fixes.

For my next role, I needed more than a functional prototype.
I needed a technical artifact that clearly demonstrates how I identify problems and make decisions in ambiguous, risk-sensitive systems.


---

## 2. Problems Observed in Production

This project is grounded in concrete issues observed while operating fraud detection systems.

### 2.1 Short-circuit Detections and Limited Visibility

Short-circuit detection evaluated rules in order and stopped at the first hit.
This approach was very efficient and correct for real-time decision-making. 

However, it introduced visibility limitations:
- Only triggered rules were observed.
- Signals from later rules were never evaluated and recorded.
- For blocklisted users, changes in transaction behavior were masked.

As a result, it became difficult to:
- observe signals that did not lead to enforcement.
- understand which rules actually contributed to detection.
- track how user behavior changed over time.

These limitations did not affect real-time correctness,
but significantly reduced the system’s ability to be analyzed and improved.

---

### 2.2 Explainable Decisions, Limited Observability

When a rule triggered, the resulting decision was explainable
through rule IDs, transaction data, and monitoring-based analysis.

However, this explainability was limited to enforced outcomes.
The system did not systematically capture:
- near-miss cases,
- non-trigger distributions,
- or rule-level behavioral signals.

Without this observational data,
detection tuning relied heavily on experience and intuition
rather than measurable evidence.

---

### 2.3 Rule Changes Were Hard to Verify

Rule changes needed to be tested under conditions equivalent to production.

However, the system lacked a production-like mechanism to:
- replay historical events,
- validate changes quantitatively,
- and observe unintended side effects safely.

This made iterative improvement slower and riskier.

---

## 3. Key Design Decisions

Based on these observations, this project focuses on three architectural decisions.

While informed by prior operational experience, it is a clean redesign intended to reproduce production behavior rather than mirror an existing implementation.

The design emphasizes what should be observable and verifiable,
rather than optimizing solely for minimal latency or immediate enforcement.

---

### 3.1 Asynchronous Detection

Detection logic beyond preliminary checks is decoupled from the request lifecycle and executed asynchronously.

This allows:
- stable ingestion regardless of detection workload,
- explicit recording of detection attempts,
- independent retry and inspection of failures.

Detection results are not immediately returned to the caller.
This trade-off improves observability, operational reliability,
and allows deferred enforcement such as post-authorization cancellation.


---

### 3.2 Separation of Detection and Decision

Detection and final decision-making are treated as separate concerns.

The system distinguishes between:
- event ingestion and preliminary checks (e.g. blocklist),
- rule evaluation (detection),
- final decision and side effects (e.g. payment blocking, blocklist registration).

Rule evaluation is recorded regardless of whether an enforcement action is taken.

This makes it possible to:
- capture evaluation results for warning or observation-only rules,
- retain near-miss and non-blocking signals,
- analyze detection behavior independently of policy decisions.

---

### 3.3 Production-Equivalent Evaluation and Replay

The rule engine is structured to support evaluation under conditions equivalent to production.

Rather than relying on simplified test logic,
rule evaluation uses the same definitions and execution path as live detection.

This enables:
- replay of historical events to validate rule changes,
- evaluation of detection behavior under production-like conditions,
- prevention of behavioral drift between test and production environments.



---

## 4. Architecture

### 4.1 Data & Control Flow

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

### 4.2 Key Principles

- Ingestion vs evaluation separation  
- Idempotent ingestion  
- Outbox as source of truth  
- Asynchronous worker evaluation  
- Clean domain modelling  

---

## 5. Domain Model

Fraud systems receive heterogeneous payloads from multiple upstream services.  
Separating Order, Purchase, and Outbox ingestion keeps the system consistent, observable, and easy to reason about.

| Entity        | Description |
|---------------|-------------|
| Order         | User-intent event with items, price, metadata |
| Purchase      | Payment attempt tied to an order |
| Outbox        | Durable event queue for async processing |
| Blocklist     | Stores account/device/card restrictions |


---

## 6. Core Components

This section explains how the design decisions in Section 3 are realized in the system.

### 6.1 Ingestion API (Synchronous Boundary)

The ingestion API accepts event snapshots and performs only lightweight validation and persistence.

Its responsibilities are intentionally limited:
- idempotent upsert of domain entities,
- creation of Outbox events,
- no heavy detection or rule execution.

This keeps the request path predictable and failure-tolerant.

---

### 6.2 Outbox & Dispatcher (Asynchronous Boundary)

The Outbox serves as the source of truth for detection work.

By persisting events before dispatch:
- ingestion remains atomic,
- lost or duplicated detection is prevented,
- replay becomes possible.

The dispatcher bridges persistence and asynchronous execution.

---

### 6.3 Celery Workers (Detection Execution)

Celery workers consume Outbox events and execute detection logic asynchronously.

This allows:
- horizontal scaling of evaluation,
- isolation of failures,
- controlled retries and inspection.

Detection execution is independent of request latency.

---

### 6.4 Rule Engine (Evaluation Logic)

The rule engine evaluates fraud conditions using a stateless, SQL-like rule model.

It is responsible only for evaluation:
- no enforcement,
- no side effects,
- no coupling to transport or persistence.

This separation enables replay, simulation, and independent verification.

---

### 6.5 Synchronous Detection Path (For Comparison)

A synchronous detection path exists for comparison and testing.

It demonstrates the behavioral difference between:
- immediate enforcement,
- and observation-first asynchronous detection.


---

## 7.	Running with Docker

This project includes a Docker Compose setup that allows you to run the API, Celery workers, Redis, and PostgreSQL together.

### 7.1 Start the stack

Run the following command from the project root:

```bash
docker compose up --build
```

This command will build all images and start:
- Django API containers
- Celery workers and Celery beat
- Redis
- PostgreSQL

Once the stack is running, the APIs are accessible from your host machine.

---

### 7.2 Synchronous detection test (block API)

The synchronous endpoint executes fraud detection during the request/response cycle and immediately returns a decision.

```bash
curl -X POST http://127.0.0.1:8000/fds/detect/order \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "order_id": "ORD123",
    "account_id": "A100",
    "device_id": "D100",
    "order_country": "JP",
    "total_price": 12000,
    "currency": "JPY",
    "order_status": "CREATED",
    "items": [
      {"product_id": "P1", "unit_price": 6000, "quantity": 2}
    ],
    "metadata": {"source": "mobile-web"}
  }'
```
Example response (will vary depending on rules you configure):

```js
{
  "decision": "allow",
  "reasons": [],
  "register_blocklist": false,
  "register_params": {
    "user": null,
    "device": null,
    "card": null
  }
}
```

---

### 7.3 Asynchronous ingestion test (Outbox + Celery)

The asynchronous path only ingests the snapshot and enqueues work.
Heavy rule evaluation is done later by Celery workers consuming Outbox events.

```bat
curl -X POST http://127.0.0.1:8000/orders \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "order_id": "ORD123",
    "account_id": "A100",
    "device_id": "D100",
    "order_country": "JP",
    "total_price": 12000,
    "currency": "JPY",
    "order_status": "CREATED",
    "items": [
      {"product_id": "P1", "unit_price": 6000, "quantity": 2}
    ],
    "metadata": {"source": "mobile-web"}
  }'
```
Expected response:

```js
{"status": "queued"}
```
What happens internally:
1.	Django upserts the Order snapshot.
2.	An Outbox row is inserted with status READY.
3.	A Celery worker picks up the Outbox batch and calls the rule engine.
4.	Results are stored in the Processed table for idempotency and audit.


---

## 8. Example Scenario

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

