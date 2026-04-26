# Материалы исследовательского эксперимента

В приложении приведены материалы, относящиеся к подготовке данных, baseline-экспериментам и сравнению обучаемых графовых моделей.

| Ноутбук | Назначение |
|---|---|
| `notebooks/scifact_dataset_eda.ipynb` | Первичный анализ корпуса SciFact, проверка структуры данных, распределений и пропусков. |
| `notebooks/scifact_retrieval_baselines.ipynb` | Сравнение BM25, semantic search и semantic + graph rerank. |
| `notebooks/scifact_graph_models.ipynb` | Подготовка графа, обучение GraphSAGE, GAT и R-GCN, подбор гиперпараметров. |

Table: Использованные исследовательские ноутбуки {#app-tbl-notebooks}

| Объект | Пример |
|---|---|
| Документ | `4983`: "Microstructural development of human newborn cerebral white matter assessed in vivo by diffusion tensor magnetic resonance imaging." |
| Запрос | `0-dimensional biomaterials lack inductive properties.` |
| Разметка | `query_id = 0`, `corpus_id = 31715818`, `relevance = 1` |

Table: Пример объектов SciFact {#app-tbl-scifact-example}

| Параметр | Значение |
|---|---:|
| Документов | 5183 |
| Запросов | 1109 |
| Размеченных пар | 1258 |
| Тестовых запросов | 300 |
| Размер фрагмента | 900 символов |
| Перекрытие фрагментов | 120 символов |
| Фрагментов после нарезки | 15893 |
| Embedding-модель | `BAAI/bge-m3` |
| Размерность embedding-вектора | 1024 |
| Извлеченных сущностей | 137401 |
| Графовых связей | 257566 |

Table: Основные параметры подготовки данных и индексации {#app-tbl-experiment-config}

![Распределения основных характеристик корпуса SciFact](assets/scifact_eda_overview.png){#app-fig-scifact-overview width=92%}

| Пайплайн | nDCG@10 | Recall@10 | Precision@10 | MRR@10 |
|---|---:|---:|---:|---:|
| BM25 / keyword | 0,6100 | 0,7367 | 0,0803 | 0,5736 |
| Semantic search | 0,6488 | 0,7811 | 0,0877 | 0,6150 |
| Semantic + graph rerank | 0,6537 | 0,7968 | 0,0897 | 0,6151 |

Table: Сводное сравнение baseline retrieval-пайплайнов {#app-tbl-baseline-results}

| Модель | alpha | nDCG@10 | Recall@10 | MRR@10 |
|---|---:|---:|---:|---:|
| Semantic + graph baseline | 0,00 | 0,6537 | 0,7968 | 0,6151 |
| GraphSAGE | 0,10 | 0,6491 | 0,7861 | 0,6126 |
| GAT | 0,00 | 0,6537 | 0,7968 | 0,6151 |
| R-GCN | 0,10 | 0,6720 | 0,8072 | 0,6358 |

Table: Сравнение обучаемых графовых архитектур {#app-tbl-gnn-results}

| hidden_dim | dropout | learning rate | alpha | test nDCG@10 | test Recall@10 | test MRR@10 |
|---:|---:|---:|---:|---:|---:|---:|
| 64 | 0,15 | 0,0010 | 0,10 | 0,6709 | 0,7989 | 0,6371 |
| 96 | 0,25 | 0,0010 | 0,10 | 0,6754 | 0,8039 | 0,6402 |
| 128 | 0,35 | 0,0005 | 0,10 | 0,6753 | 0,8112 | 0,6386 |

Table: Подбор гиперпараметров R-GCN {#app-tbl-rgcn-tuning}
