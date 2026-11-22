# =====================================================================
# Laboratorio LLMOps - automatización
#   Primera vez:  make all     (levanta, descarga modelos, corre el pipeline y prueba)
#   Día a día:    make up  /  make ask  /  make down  /  make status
# =====================================================================

SHELL := /bin/bash

# Puertos: .env (copiado de .env.example) los define
-include .env
API_PORT        ?= 8020
UI_PORT         ?= 8502
MLFLOW_PORT     ?= 5001
PROMETHEUS_PORT ?= 9091
GRAFANA_PORT    ?= 3001
OLLAMA_PORT     ?= 11435

API        := http://localhost:$(API_PORT)
UI         := http://localhost:$(UI_PORT)
MLFLOW     := http://localhost:$(MLFLOW_PORT)
PROMETHEUS := http://localhost:$(PROMETHEUS_PORT)
GRAFANA    := http://localhost:$(GRAFANA_PORT)
LLM        := qwen2.5:1.5b
EMBEDDING  := nomic-embed-text
PY         := .venv/bin/python

Q ?= ¿Cada cuánto se realiza el mantenimiento preventivo?
K ?= 3
T ?= 0.2

.DEFAULT_GOAL := help
.PHONY: help all setup up down restart status models pipeline index ask eval experimentos test logs open clean

help: ## Muestra esta ayuda
	@echo "Uso: make <comando>"
	@echo
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*## "}{printf "  \033[36m%-13s\033[0m %s\n", $$1, $$2}'

all: up models pipeline ask open ## Primera vez: levanta todo, descarga modelos, corre el pipeline, pregunta y abre el navegador

setup: ## Crea .env y el entorno local para los scripts de evaluación
	@docker info >/dev/null 2>&1 || { echo "  ✗ Docker no está corriendo. Abre Docker Desktop."; exit 1; }
	@test -f .env || { cp .env.example .env; echo "  ✓ .env creado desde .env.example"; }
	@test -x $(PY) || { command -v uv >/dev/null || { echo "Instala uv: brew install uv"; exit 1; }; \
		uv venv -q --python 3.11 .venv && uv pip install -q --python $(PY) requests && echo "  ✓ .venv listo"; }

up: setup ## Construye y levanta los seis servicios
	@echo "→ Levantando ollama, mlflow, api, ui, prometheus y grafana..."
	@docker compose up -d --build --quiet-pull >/dev/null 2>&1 || { docker compose up -d --build; exit 1; }
	@for i in $$(seq 1 90); do curl -sf -o /dev/null $(API)/health && break; \
		[ $$i -eq 90 ] && { echo "  ✗ La API no respondió. Revisa: make logs"; exit 1; }; sleep 2; done
	@for i in $$(seq 1 30); do curl -sf -o /dev/null $(UI)/_stcore/health && break; sleep 1; done
	@$(MAKE) --no-print-directory status

down: ## Apaga todo (conserva modelos, trazas y métricas)
	@docker compose down >/dev/null 2>&1; echo "✓ Apagado. Los volúmenes se conservan."

restart: down up ## Reinicia todo

status: ## Estado de cada servicio
	@echo
	@check() { if curl -sf -o /dev/null -m 3 "$$2"; then s="\033[32m● arriba\033[0m"; else s="\033[31m○ abajo \033[0m"; fi; printf "  %-11s $$s  %s\n" "$$1" "$$3"; }; \
	check Ollama     http://localhost:$(OLLAMA_PORT)/api/version  "http://localhost:$(OLLAMA_PORT)"; \
	check API        $(API)/health                    $(API)/docs; \
	check Chat       $(UI)/_stcore/health             $(UI); \
	check MLflow     $(MLFLOW)/health                 $(MLFLOW); \
	check Prometheus $(PROMETHEUS)/-/ready            $(PROMETHEUS)/targets; \
	check Grafana    $(GRAFANA)/api/health            "$(GRAFANA)  (admin/admin)"
	@echo

models: ## Descarga qwen2.5:1.5b y nomic-embed-text en Ollama (solo la primera vez)
	@for m in $(LLM) $(EMBEDDING); do \
		docker compose exec -T ollama ollama list | grep -q "^$$m" \
			&& echo "  • $$m ya está descargado" \
			|| { echo "→ Descargando $$m..."; docker compose exec -T ollama ollama pull $$m >/dev/null 2>&1 && echo "  ✓ $$m"; }; \
	done

pipeline: ## Indexa: documentos -> bronze -> silver -> gold -> índice SQLite
	@echo "→ Pipeline de indexación..."
	@docker compose exec -T api python main.py 2>&1

index: setup ## Corre el mismo pipeline a través de la API (POST /indexar)
	@echo "→ Indexando documentos..."
	@API_URL=$(API) $(PY) app/cliente.py indexar

ask: setup ## Hace una pregunta al RAG.  Ej: make ask Q="¿Cuál es el inventario de seguridad?" K=3 T=0.2
	@API_URL=$(API) $(PY) app/cliente.py preguntar "$(Q)" $(K) $(T) \
		|| echo "  ✗ Falló la consulta. ¿Corriste make models y make pipeline?"

eval: setup ## Corre las 8 preguntas de referencia y guarda evaluacion/resultados/evaluacion.json
	@API_URL=$(API) $(PY) evaluacion/evaluacion.py

experimentos: setup ## Experimentos A, B y C: top_k, temperatura y preguntas sin evidencia
	@for e in topk temperatura sin_evidencia; do echo "→ Experimento $$e"; API_URL=$(API) $(PY) evaluacion/experimentos.py $$e || exit 1; done

test: ## Corre los tests del pipeline y del RAG dentro del contenedor de la API
	@docker compose exec -T api python -m pytest -q -p no:cacheprovider tests

logs: ## Sigue los logs de la API
	@docker compose logs -f --tail 50 api

open: ## Abre el chat, Swagger, MLflow y el dashboard de Grafana
	@open $(UI) $(API)/docs $(MLFLOW) "$(GRAFANA)/d/llmops-ollama-rag"

clean: ## Apaga todo y BORRA los volúmenes (modelos descargados, trazas y métricas) y las salidas del pipeline
	@docker compose down -v >/dev/null 2>&1
	@rm -f ./data/bronze/*.txt ./data/bronze/*.csv ./data/silver/*.csv ./data/gold/*.csv ./data/gold/*.json ./data/gold/*.db ./logs/pipeline.log
	@echo "✓ Volúmenes y capas borrados (se conserva la evidencia de evaluacion/resultados/). 'make all' vuelve a descargar los modelos."
