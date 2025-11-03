## Fraud Detection System (FDS)

📌 **Overview**  
This project is a **Fraud Detection System (FDS) prototype** reimplemented in **Python**, based on my experience with **Java-based FDS platforms in production**.  

It demonstrates:  
- Rule-based detection of suspicious transactions  
- Dynamic reporting of chargeback rates and fraud trends  
- Fraud response automation: block/allow decisions with blocklist and transaction updates  
- Modular, data-driven rule execution and in-memory caching for performance  

---

🎯 **Motivation**  
In real operations, I found recurring issues:  
- Fraud reports required repetitive manual queries for each entity  
- Inconsistent JSON formats made automation difficult  
- Adding or modifying rules required code-level changes  

---

🏗️ **System Architecture**

- **Data Collector**: Normalizes and stores transactional logs (Order, Purchase)
- **Rule Engine (Detector)**: Applies fraud rules (frequency checks, country mismatch, blacklist hits)
- **Blocklist Manager**: Maintains user/device/card blocklists
- **Chargeback Report Generator**: Automates fraud reporting with dynamic query composition
- **Dashboard/Visualization**: For visualization of fraud trends and rule hits

---

🔍 **Detection Logic (Real-time)**  

1. **Collect** `Order` (initial) or `Purchase` (settlement) data via API.
2. **Normalize** into a unified model `CaseParams`:
   ```python
   class CaseParams(BaseModel):
       kind: CaseKind             # "order" | "purchase"
       case_id: str               # order_id or purchase_id
       refs: EntityRefs           # user/device/card references
   ```
3. **Check Blocklist** – verifies user, device, and card against stored blocklists.  
4. **Evaluate Rules** – executes in-memory SQL rules
5. **Merge Hits → Result** – combines all rule hits into a final outcome:
   ```python
   @dataclass
   class Hit:
       rule_id: str
       decision: Decision
       reason: str = ""
       register_targets: RegisterTarget = RegisterTarget.NONE
   ```
   ```python
   class Result(BaseModel):
       decision: Decision
       reasons: List[str] = []
       register_blocklist: bool = False
       register_params: RegisterParams = RegisterParams()
   ```
6. **Register Blocklist** – automatically inserts IDs (user, device, card)  
   into the blocklist based on rule results.  
7. **Return Decision** – The API responds with `ALLOW`, `REVIEW`, or `BLOCK` and reasons.

---

📊 **Chargeback Report Workflow**  

The same normalized schema is reused for analytical reporting.  

**Step 1. Target Extraction (SQL)**  
```sql
SELECT country, SUM(amount) AS total
FROM Payments
GROUP BY country
ORDER BY total DESC
LIMIT 30;
```

**Step 2. Dynamic Sub-Query Generation (SQL)**  
```sql
SELECT strftime('%Y-%m', payment_date) AS month,
       country,
       COUNT(*) AS total_payment,
       SUM(CASE WHEN is_chargeback = 1 THEN 1 ELSE 0 END) AS chargeback_count,
       (1.0 * SUM(CASE WHEN is_chargeback = 1 THEN 1 ELSE 0 END) / COUNT(*)) AS chargeback_rate
FROM Payments
WHERE country = 'Argentina'
GROUP BY month, country
ORDER BY month;
```

**Step 3. Query Composition (Python)**  
```python
def generate_subqueries(top_countries):
    queries = []
    for c in top_countries:
        query = f"""
        SELECT strftime('%Y-%m', payment_date) AS month,
               '{c}' AS country,
               COUNT(*) AS total_payment,
               SUM(CASE WHEN is_chargeback = 1 THEN 1 ELSE 0 END) AS chargeback_count,
               (1.0 * SUM(CASE WHEN is_chargeback = 1 THEN 1 ELSE 0 END) / COUNT(*)) AS chargeback_rate
        FROM Payments
        WHERE country = '{c}'
        GROUP BY month;
        """
        queries.append(query)
    return queries
```

**Step 4. Visualization**  
- Combine query results into a dataset
- render in Dash / Streamlit dashboards  


---

🚀 **Future Roadmap**  

#### Detection & Rule Management  
- Rule testing workflow (simulate → staged apply → production)  
- Hot-reload rule cache without downtime  
- Rule performance metrics and A/B testing  

#### Advanced Analytics  
- Machine learning–based anomaly detection models  
- Real-time fraud trend dashboards  
- Dynamic reporting dimensions (region, BIN, device, merchant)

#### Infrastructure  
- Cloud deployment via AWS Lambda or Docker  
- Redis-based distributed rule cache  
- Async event pipeline (Celery or Kafka)  
- CI/CD pipeline with automated regression tests  
