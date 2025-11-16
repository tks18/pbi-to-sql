# 🚀 **pbi-to-sql**

#### _"Stop letting Power BI hide your data. Turn your semantic model into a full SQL + AI powerhouse."_

Meet **pbi-to-sql** — the **next-gen RAG infrastructure tool** that extracts your _entire_ Power BI Semantic Model and rebuilds it into a **high-performance SQLite database with an embedded AI semantic layer.**

Your RAG agent finally gets context.
Your data model finally gets freedom.
Your analytics stack finally levels up.

Repo: **[https://github.com/tks18/pbi-to-sql](https://github.com/tks18/pbi-to-sql)**

---

## ✨ **Why This Exists**

Your dashboards look fire, sure.
But your RAG AI?

It’s starving.
It can’t see your model.
It doesn’t understand your joins.
It has no idea why f_ExpenseTransactions and d_ExpenseCategory even vibe.

**pbi-to-sql fixes all of that** by:

1. Extracting **tables, columns, relationships, metadata** from `.tmdl`
2. Rebuilding the whole thing as a **legit relational SQL database**
3. Using **local LLMs** to generate **semantic summaries for every table + relationship**
4. Embedding all that semantic gold _directly inside the DB_

Your AI doesn’t guess anymore —
it **queries meaning**.

---

## 🔥 **This Thing Slaps (Features)**

### **1. Full-Blown TMDL Parsing**

This is not a CSV yeeter. This is a full semantic model interpreter.

- Reads all your table definitions
- Maps PBI types → SQLite (INTEGER, REAL, TEXT)
- Parses relationships from the relationships folder
- Recreates them with actual foreign keys
- Handles cursed cyclical dependencies using **DEFERRABLE FKs**

If your PBIX understands it, **pbi-to-sql** rebuilds it.

---

### **2. The AI Semantic Layer 🧠 (The Main Character)**

This is where the app goes from tool → platform.

Everything runs **100% locally** using `langchain` + `ollama` + SLMs like `gemma:4b`.

#### What it generates:

- **rag_model_summary**
  High-level overview of the entire semantic model.

- **rag_table_summaries**
  Table-by-table AI summaries, including:

  - purpose
  - key fields
  - relationship roles
  - fact/dimension classification
  - JSON semantic descriptors

- **Context-Aware Relationship AI**
  For every relationship, the AI:

  1. Summarizes Table A
  2. Summarizes Table B
  3. Re-combines both summaries
  4. Produces a natural-language relationship meaning

Example:

> `"This links each expense transaction to its specific sub-category for downstream spend analysis."`

#### And the killer feature:

All of these summaries are **stored directly inside the database** as regular SQL tables.

Your RAG agent can literally:

```sql
SELECT summary
FROM rag_table_summaries
WHERE table_name = 'f_ExpenseTransactions';
```

No hallucinations.
No blind spots.
No guessing.

---

### **3. Boujee RAG-Ready Docs 📄**

Automatically generated:

- `ai_model_summary.md` — full AI-crafted overview
- Table catalog
- Fact vs Dimension classifications
- Relationship explanations
- A **RAG Query Guide** with explicit JOIN recipes

Clean. Readable. Actually useful.

---

### **4. Modular AF Architecture (The Glow-Up 💅)**

This isn’t some 900-line Python file glued together with vibes.

#### Architecture includes:

- **Adapters** → DB integrations (SQLite today, Postgres tomorrow)
- **Service Layer** → ingestion logic + semantic analysis
- **Pipeline Layer** → reusable ingestion workflows
- **Config Layer** → index, incremental, semantic settings

Want Postgres?
Just finish the `PostgresAdapter` stub.
No rewrite needed.

---

### **5. Multiple Pipelines = Pick Your Adventure 🧩**

- **FullIngestionPipeline**
  Rebuilds everything: schema + data + semantics.

- **SchemaOnlyPipeline**
  Creates tables, metadata, and relationships only.

- **DataOnlyPipeline**
  Fast refresh — loads new CSVs into existing schema.

- **SemanticPipeline**
  Runs only the AI analysis (the expensive but high-value part).

Flexible enough for GUIs, APIs, cron jobs, or agent workflows.

---

### **6. A CLI That Doesn’t Make You Cry**

Just run:

```bash
python main_cli.py
```

It asks:

- TMDL folder
- CSV folder
- Output directory
- Whether to recreate or refresh
- Whether to generate docs
- Whether to run AI semantic analysis

Then it vibecrafts your entire RAG database.

---

## 🚀 **Usage**

### **Prerequisites**

- Install **Ollama**
- Pull a model (Gemma recommended):

```bash
ollama pull gemma:4b
```

### **Installation**

```bash
git clone https://github.com/tks18/pbi-to-sql
cd pbi-to-sql
pip install -r requirements.txt
```

### **Run**

```bash
python main_cli.py
```

### **You Get:**

- `pbi_model.sqlite` — data + schema + AI semantic layer
- `data_dictionary.md` — table reference
- `ai_model_summary.md` — boujee AI docs
- `incremental.yaml` & `index_config.yaml`

Everything in one clean output folder.

---

## 🔮 **The Next Szn (Roadmap)**

- [ ] Real PostgresAdapter implementation
- [ ] FastAPI semantic & ingestion backend
- [ ] Streamlit / Gradio GUI
- [ ] Auto diagram generator (ERD + semantic maps)
- [ ] Never let your RAG agent be mid ever again

---

## 👤 **Author**

Made by people who looked at a PBIX and said:

> “Why is this locked inside a GUI? Let me unleash the data.”

If you relate… welcome home.

Author: **[Sudharshan TK](https://github.com/tks18) 💖**

Repo: **[https://github.com/tks18/pbi-to-sql](https://github.com/tks18/pbi-to-sql)**

---

## ⭐ **Final Note**

This isn’t ETL.
This is a **data model emancipation engine**.
It frees your PBIX from its GUI prison and turns it into a queryable, AI-aware dataset anywhere you want.

Your dashboards? Still cute.
Your SQL + RAG stack? **Absolutely unstoppable.**

If you want a version with badges, architecture diagrams, or an ASCII art intro — tell me.
