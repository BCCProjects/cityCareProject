# City Care Backend

Backend do MVP da plataforma City Care, construÃ­do com Django e Django REST Framework. O objetivo Ã© registrar, acompanhar e auditar ocorrÃªncias urbanas abertas por cidadÃ£os, garantindo fluxo de trabalho estruturado para o Ã³rgÃ£o pÃºblico responsÃ¡vel.

## VisÃ£o geral do domÃ­nio

| Entidade | DescriÃ§Ã£o |
| --- | --- |
| **Department** | Representa Ã³rgÃ£os/setores responsÃ¡veis pela triagem das ocorrÃªncias. |
| **Category** | Tipos de ocorrÃªncia vinculados a um departamento (ex.: IluminaÃ§Ã£o, Obras). |
| **Tag** | Marcadores escolhidos pelo cidadÃ£o ao abrir uma ocorrÃªncia (Buraco, Entulho etc.). |
| **Citizen** | UsuÃ¡rio do aplicativo mÃ³vel com autenticaÃ§Ã£o via JWT dedicada. |
| **Administrator** | UsuÃ¡rio do Ã³rgÃ£o resolutor autenticado no Django Admin. |
| **Report** | OcorrÃªncia em si, com status, prioridade, endereÃ§o, coordenadas e relaÃ§Ã£o N:N com tags. |
| **Attachment** | Fotos anexadas pelo cidadÃ£o. |
| **Comment** | ComentÃ¡rios pÃºblicos adicionados pelo cidadÃ£o. |
| **StatusHistory** | Linha de auditoria para cada transiÃ§Ã£o de status, registrando responsÃ¡vel e notas. |

O fluxo de status segue **ABERTO â†’ ANALISANDO â†’ DEFERIDO â†’ EM_ANDAMENTO â†’ CONCLUÃDO** com ramificaÃ§Ãµes para **INDEFERIDO** e marcaÃ§Ã£o manual como **IGNORADO** quando ultrapassar 168 horas sem atualizaÃ§Ã£o.

## Arquitetura em camadas

```
core/
â”œâ”€â”€ reports/          # Models, admin e migraÃ§Ãµes do domÃ­nio de ocorrÃªncias
â”œâ”€â”€ repositories/     # Consultas SQL parametrizadas e agregaÃ§Ãµes
â”œâ”€â”€ services/         # Regras de negÃ³cio e transaÃ§Ãµes (ex.: mudanÃ§as de status)
â””â”€â”€ api/              # Serializers, autenticaÃ§Ã£o e viewsets DRF
accounts/             # Modelos e endpoints de cadastro/autenticaÃ§Ã£o
```

- **Camada de serviÃ§os** (`ReportService`) centraliza regras de transiÃ§Ã£o, bloqueios (`select_for_update`), validaÃ§Ã£o de fluxo e registro em `StatusHistory`.
- **RepositÃ³rios** expÃµem consultas SQL puras exigidas pelo projeto (elegÃ­veis para ignorado, mÃ©dia de resoluÃ§Ã£o, agrupamentos por bairro e sÃ©rie semanal).
- **API** expÃµe apenas endpoints necessÃ¡rios ao aplicativo do cidadÃ£o. Toda autenticaÃ§Ã£o exige cabeÃ§alhos `X_USER`, `X_APP`, `X_SIGNATURE` definidos no `.env`.
- **Admin Django** Ã© utilizado exclusivamente pelo Ã³rgÃ£o pÃºblico para triagem e atualizaÃ§Ã£o de status.

## Consultas SQL principais

1. **RelatÃ³rios elegÃ­veis para marcaÃ§Ã£o como ignorado** (`core.repositories.report_repository.get_reports_eligible_for_ignore`).
2. **Tempo mÃ©dio de resoluÃ§Ã£o por categoria** (`core.repositories.report_repository.get_average_resolution_time_by_category`).
3. **Abertos agrupados por bairro/prioridade** (`core.repositories.report_repository.get_open_reports_grouped_by_neighborhood`).
4. **SÃ©rie temporal semanal por status** (`core.repositories.report_repository.get_weekly_series_by_status`).

A migraÃ§Ã£o `0002_database_objects` ainda cria:
- FunÃ§Ã£o `calculate_sla_hours` (MySQL) para calcular SLA em horas a partir de `due_at`.
- View `report_status_overview` para contagem por categoria e status.

## ConfiguraÃ§Ã£o

1. Copie o arquivo `.env.example` para `.env` e ajuste os valores, incluindo as chaves de seguranÃ§a dos cabeÃ§alhos.
2. Instale as dependÃªncias listadas em `requirements.txt`.
3. Execute as migraÃ§Ãµes: `python manage.py migrate`.
4. Crie um superusuÃ¡rio administrador: `python manage.py createsuperuser`.
5. Inicie o servidor: `python manage.py runserver`.

### Banco de dados

- **ProduÃ§Ã£o**: defina `DB_ENGINE=mysql` e configure `MYSQL_*` para utilizar MySQL.
- **Testes/Desenvolvimento rÃ¡pido**: mantenha `DB_ENGINE=sqlite` para usar SQLite em arquivo local.

## AutenticaÃ§Ã£o

- **CidadÃ£os**: `POST /api/auth/citizens/register` e `POST /api/auth/citizens/token` retornam pares JWT personalizados (scope `citizen`).
- **Administradores**: `POST /api/auth/admins/register` cria usuÃ¡rios do Ã³rgÃ£o (login pelo Django Admin). Todos os endpoints de cadastro/token exigem os cabeÃ§alhos `X_USER`, `X_APP`, `X_SIGNATURE`.

## Endpoints principais

| MÃ©todo | Caminho | DescriÃ§Ã£o |
| --- | --- | --- |
| `GET` | `/api/categories/` | Lista categorias com departamento. |
| `GET` | `/api/tags/` | Lista tags disponÃ­veis. |
| `POST` | `/api/reports/` | Cria ocorrÃªncia com tags e anexos (multipart). |
| `GET` | `/api/reports/` | Lista ocorrÃªncias do cidadÃ£o com filtros de status e categoria. |
| `GET` | `/api/reports/{id}/` | Detalhe completo da ocorrÃªncia. |
| `POST` | `/api/reports/{id}/comments/` | Adiciona comentÃ¡rio pÃºblico. |
| `GET` | `/api/reports/eligibles-ignore` | Consulta relatÃ³rios elegÃ­veis a serem ignorados (param `hours`). |
| `GET` | `/api/reports/avg-resolution/` | MÃ©dia de resoluÃ§Ã£o por categoria em horas. |
| `GET` | `/api/dashboard/` | Dados agregados (abertos por bairro/prioridade e sÃ©rie semanal).

A coleÃ§Ã£o Postman (`postman/CityCare.postman_collection.json`) e o environment (`postman/CityCare.postman_environment.json`) jÃ¡ trazem todas as chamadas com variÃ¡veis preparadas.

## Testes automatizados

```
pytest
```

Os testes cobrem o fluxo completo de status, validação de indeferimento, consulta de elegibilidade para ignorado e criação com múltiplas tags/anexos.
O `pytest` já traz `pytest-cov`, gerando `coverage.xml` na raiz e permitindo visualizar linhas faltantes com `pytest --cov-report=term-missing`. Toda a suíte de testes fica organizada em `tests/`, no mesmo nível do `manage.py`.
## DocumentaÃ§Ã£o adicional

- `requirements.txt`: dependÃªncias do projeto.
- `.env.example`: base para configuraÃ§Ã£o de ambiente.
- MigraÃ§Ãµes incluem constraints `CHECK` para latitude/longitude, unicidade de tags/categorias e criaÃ§Ã£o da funÃ§Ã£o SQL e view de suporte.

## PrÃ³ximos passos sugeridos

- Integrar armazenamento de mÃ­dia externo.
- Construir painel web para o Ã³rgÃ£o reaproveitando os serviÃ§os existentes.
- Automatizar job de marcaÃ§Ã£o como ignorado usando o serviÃ§o transacional quando o escopo permitir.








