# Changelog

All notable changes to this project will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

## [1.0.0](https://github.com/tks18/pbi-to-sql/compare/v0.1.0...v1.0.0) (2025-11-16)


### Build System 🏗

* **packages:** add langchain & ollama ([bbba9a3](https://github.com/tks18/pbi-to-sql/commit/bbba9a3415ad457328c69e5d348a377c99dc071b))


### Features 🔥

* **app/adapters:** update adapters to add new RAG Tables to DB ([6442fc3](https://github.com/tks18/pbi-to-sql/commit/6442fc3d4ab8eed9fbcb3fb736a5973b854c75db))
* **app/core:** modularize the app, move the core modules to core folder ([5707fc9](https://github.com/tks18/pbi-to-sql/commit/5707fc9c82d6c987e46f77957f06845ccf9a0b53))
* **app/core:** move the doc generator and write it to use AI to create rich summaries ([84cf98c](https://github.com/tks18/pbi-to-sql/commit/84cf98c7a6f933de816acac71a67a8f4dfef6154))
* **app/pipelines:** build various pipelines which can be consumed by the future applications ([ed667c5](https://github.com/tks18/pbi-to-sql/commit/ed667c5dfafdcecff0f40dd5634cf4867b009f93))
* **app/services:** build a semantic service pipeline to build all AI summaries and embed in DB ([e58d8e9](https://github.com/tks18/pbi-to-sql/commit/e58d8e9fc66afedcc15336c46f1c8a86787c46b9))
* **app/services:** move the metadata mgr to service in ingestion itself ([80df2b8](https://github.com/tks18/pbi-to-sql/commit/80df2b8f60f61f4d4507c53bd3f717977c139bd7))
* **dags:** build a dag workflow for apache-airflow ([e9cebd3](https://github.com/tks18/pbi-to-sql/commit/e9cebd3a7d797e39240a1e4392a6fa0dab1ea76b))
* **main:** use the updated API to access all the modules and implement AI workflows as well ([4229392](https://github.com/tks18/pbi-to-sql/commit/4229392d2019f2e468f06a61a2bc17c177b90ab8))
* **types:** write more robust types for the app with pydantic ([7a424ec](https://github.com/tks18/pbi-to-sql/commit/7a424ec8deb344a130a4ccab9c5b4bab97d2e9b5))


### Others 🔧

* update project version ([a52941d](https://github.com/tks18/pbi-to-sql/commit/a52941dacb901e1d49af19bde7001a4047b40055))
* update project.toml version ([a495e1c](https://github.com/tks18/pbi-to-sql/commit/a495e1c9a99d405870b6f91a48056de176fbd200))

## 0.1.0 (2025-11-16)


### CI 🛠

* **husky/cz:** add husky, cz for standardized git commits and versioning ([c2336d6](https://github.com/tks18/pbi-to-sql/commit/c2336d65144a35c67b2f773183dcf5fd9365db11))


### Docs 📃

* **license:** add license for the project ([4c54e01](https://github.com/tks18/pbi-to-sql/commit/4c54e0103c5760b9aff5868aa0ea026c6b8912db))
