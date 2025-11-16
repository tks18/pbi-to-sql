# 🚀 pbi-to-sql

### _"Turn your Power BI model into a fully queryable SQL database — like a data wizard, but with Gen Z energy."_

---

## 🧠 What Even _Is_ This?

**pbi-to-sql** is your new data pipeline bestie.
It takes your **Power BI Semantic Model (.tmdl)** + **CSV exports**, reverse-engineers the whole thing, and builds a **SQLite database** that:

- Preserves **tables**
- Preserves **columns**
- Preserves **relationships**
- Preserves **metadata**
- Preserves **your sanity** 🧘‍♂️

Basically: everything your PBIX knows, but now it’s SQL-native.

Perfect for:

- AI pipelines 🤖
- Analytics automation 📊
- Local RAG systems 🔍
- Query engines (DuckDB, SQLite extensions, mother of all joins) 🔥
- Replacing Power BI for backend workflows (bold but fair) 💼

---

## ✨ Core Features

### 🧩 Modular Architecture (SRP-friendly AF)

- TMDL parsing
- Relationship extraction
- Table metadata
- CSV loaders
- SQLite schema builder
- Index engine
- Metadata catalog
- Pipeline orchestrator

Everything is a class.
Everything has a job.
Nothing cries internally. 😌

---

## 🔥 Why This Exists

Because Power BI is **amazing for visuals**,
but terrible when you’re like:

> "Hmm, I wish I could run LLMs directly on my model."

Or:

> "Would be nice if this was just SQL."

This project says **say less fam** 🙏 and gives you exactly that.

---

## 🎯 Roadmap (aka "things we’ll definitely oversell in the next demo")

- 🔌 **FastAPI service layer** — run pipelines from an API
- 📚 **Auto SQL docs** — generate a live data dictionary
- 🧬 **ML/AI Mode** — embeddings, vector search, RAG integrations
- 🎛️ **DuckDB backend** — because speed matters
- 📡 **Streaming ingestion** — real-time Power BI → SQL
- 🧪 **Full unit-testing suite**

Yeah… we’re basically building the next mini dbt.

---

## 💅 Aesthetic Philosophy

- Zero boilerplate.
- Zero "enterprise complexity for no reason".
- Maximum modularity.
- Maximum vibes.

---

## 👤 Author

Built for analysts, audit nerds, data engineers, and anyone who looked at a PBIX one day and said:

> "I wish I could SQL this."

This repo: **grants that wish**. 🪄

---

## ⭐ Final Note

If you break something, it’s not your fault.
If everything works perfectly? Absolutely take credit for it.

Happy querying ✨
