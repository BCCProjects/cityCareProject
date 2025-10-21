# City Care Backend

Este repositório contém o MVP do backend do City Care, uma plataforma de
participação cidadã para registro e acompanhamento de ocorrências urbanas.

## Arquitetura

- **Django + Django REST Framework** estruturam a API pública.
- **MySQL** é o banco principal (com suporte a SQLite para testes) configurado
  via variáveis de ambiente em `.env`.
- A camada de domínio fica em `core/reports`, com separação explícita em
  modelos, repositórios (consultas SQL cruas), serviços e views da API.
- A autenticação usa JWT (SimpleJWT). O órgão público utiliza exclusivamente o
  Django Admin para triagem.

## Modelagem principal

| Entidade | Descrição |
| --- | --- |
| `Department` | Órgão responsável pela categoria. |
| `Category` | Categoria de ocorrência vinculada a um departamento. |
| `Tag` | Marcadores definidos pelo cidadão. |
| `Report` | Ocorrência registrada com fluxo de status, endereço e geolocalização. |
| `Comment` | Comentário público do cidadão. |
| `Attachment` | Anexos de imagem da ocorrência. |
| `StatusHistory` | Histórico auditável de transições de status. |

As constraints do banco garantem unicidade, domínios válidos para latitude e
longitude e enumeração restrita para `status` e `priority`.

## Consultas SQL

A classe `ReportRepository` expõe as consultas exigidas:

1. `get_reports_eligible_for_ignore(hours)` — retorna ocorrências elegíveis para
   marcação como ignoradas (SQL cru parametrizado).
2. `get_average_resolution_time_by_category()` — média de tempo de resolução por
   categoria para ocorrências concluídas (SQL cru parametrizado).
3. `get_open_reports_by_neighborhood_and_priority()` — agrupamento por bairro e
   prioridade (ORM).
4. `get_weekly_status_series()` — série temporal semanal por status (ORM).

## Funções e views SQL

A migration inicial cria a função `sla_hours_remaining(due_at)` (somente em
MySQL) e a view `report_status_dashboard`, permitindo consumir métricas de SLA e
contagens por status/categoria.

## Endpoints principais

- `POST /api/auth/token/` — geração de tokens JWT.
- `GET /api/categories/` — lista de categorias com departamento.
- `GET /api/tags/` — lista de tags disponíveis.
- `POST /api/reports/` — cria uma ocorrência com tags e anexos.
- `GET /api/reports/` — lista paginada de ocorrências do cidadão com filtros de
  status e categoria.
- `GET /api/reports/{id}/` — detalhe completo da ocorrência.
- `POST /api/reports/{id}/comments/` — adiciona comentário público.

## Testes

Os testes em `core/reports/tests` cobrem o fluxo de status, obrigações de
motivo, elegibilidade para ignorado e criação de ocorrência com N:N e anexos.

Para executar:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py test
```

## Configuração rápida

Crie um arquivo `.env` com, por exemplo:

```env
DB_ENGINE=mysql
DB_NAME=city_care
DB_USER=citycare
DB_PASSWORD=citycare
DB_HOST=127.0.0.1
DB_PORT=3306
JWT_ACCESS_MINUTES=30
JWT_REFRESH_DAYS=7
```

Durante o desenvolvimento local e nos testes automatizados o projeto usa
SQLite automaticamente.
