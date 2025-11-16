# 🚀 **pbi-to-sql**

### **_"Power BI → SQL → AI. Your Semantic Model Just Got an Upgrade."_**

Transform your **Power BI Semantic Model** into a **fully queryable SQL database** — with structure, relationships, metadata, and tech swagger intact.

This is not another exporter.
This is a **semantic reconstruction engine** for modern AI + analytics stacks.

---

## 🧠 **What Even _Is_ This?**

**pbi-to-sql** takes your `.tmdl` files + CSV data dumps and rebuilds your Power BI model into a **relational SQLite database** that your tools _actually_ understand.

It ingests:

- Tables
- Columns
- Data Types
- Relationships
- Metadata

…and produces:

- A structured, schema-accurate SQL database
- Indexes + optimized relationships
- A metadata catalog
- RAG-ready semantic context (coming soon 👀)

Perfect for:

- Local RAG frameworks
- AI agents & LLM query engines
- Analytics automation
- DuckDB/SQLite extensions
- Anything that loves SQL more than PBIX

Think of it as giving your PBIX a second life — one where it speaks fluent SQL.

---

## ✨ **Core Features**

### 🔍 **1. TMDL Parsing That Goes Hard**

Fully reverse-engineers your semantic model:

- Extracts tables & data types
- Resolves relationships (one-to-many, many-to-many, bidirectional ― we don’t judge)
- Handles circular references gracefully
- Maps everything to clean SQLite types

Your model isn’t “converted.”
It’s **rebuilt**.

---

### 🧱 **2. Modular Architecture (built like a real product)**

Breakdown of components:

- **TMDL Parser** – extracts model definitions
- **Relationship Engine** – reconstructs FK logic
- **Metadata Layer** – catalogues schema, fields & lineage
- **CSV Loader** – hydrates the database
- **Schema Builder** – creates SQL structures
- **Index Manager** – performance tuning
- **Pipeline Orchestrator** – reusable ops with zero chaos

Everything has a single job.
Nothing cries internally. 😌

---

### ⚡ **3. Pipelines That Adapt to Your Workflow**

Pick your mood:

- **Full Ingestion** — rebuild from scratch
- **Schema Only** — generate tables + relationships
- **Data Only** — refresh data without touching structure
- **Semantic Mode (coming soon)** — AI-powered table summaries + RAG metadata

Scalable. Clean. Predictable.

---

### 🛠️ **4. Developer-First CLI**

A simple, interactive launcher:

```bash
python main_cli.py
```

It asks:

- Where your TMDL lives
- Where your CSVs live
- Where you want the output

Then handles everything like a responsible adult.

---

## 🔥 **Why This Exists**

Because Power BI is amazing for dashboards
…but terrible if you want:

- SQL access
- AI-ready metadata
- Local LLM reasoning
- Automated analytics pipelines
- Something other tools can actually query

We all know the moment:

> “Damn… I wish I could just SQL this PBIX.”

Well — congratulations.
**Wish granted.** 🪄

---

## 🎯 **Roadmap (a.k.a. “features we’ll definitely hype in the next demo”)**

- 🔌 FastAPI ingestion/semantic service
- 📚 Auto-generated SQL documentation
- 🧬 Embeddings & vector-search mode
- ⚡ DuckDB backend for high-performance workflows
- 📡 Streaming ingestion (Power BI → SQL → AI in real time)
- 🧪 Full unit-testing suite for the ops-nerds
- 🤖 Built-in semantic layer enrichment for RAG

Basically:
Tiny dbt + tiny Airbyte + tiny semantic layer engine.

---

## 💅 **Design Philosophy**

- No over-engineering for clout
- Modular, composable, dev-friendly
- Local-first mindset
- Maximum vibes — minimum friction

---

## 👤 **Author**

Made by people who looked at a PBIX and said:

> “Why is this locked inside a GUI? Let me unleash the data.”

If you relate… welcome home.

Author: **[Sudharshan TK](https://github.com/tks18) 💖**

Repo: **[https://github.com/tks18/pbi-to-sql](https://github.com/tks18/pbi-to-sql)**

---

## ⭐ **Final Note**

If something breaks?
That’s a feature — you just discovered a new workflow.

If everything works flawlessly?
Claim full credit. You’re the hero now.

Happy querying ✨
