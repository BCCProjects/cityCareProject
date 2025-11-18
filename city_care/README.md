# City Care Backend

Backend do MVP da plataforma City Care, construído com Django e Django REST Framework. O objetivo é registrar, acompanhar e auditar ocorrências urbanas abertas por cidadãos, garantindo fluxo de trabalho estruturado para o órgão público responsável.

## Visão geral do domínio

| Entidade | Descrição |
| --- | --- |
| **Department** | Representa órgãos/setores responsáveis pela triagem das ocorrências. |
| **Category** | Tipos de ocorrência vinculados a um departamento (ex.: Iluminação, Obras). |
| **Tag** | Marcadores escolhidos pelo cidadão ao abrir uma ocorrência (Buraco, Entulho etc.). |
| **Citizen** | Usuário do aplicativo móvel com autenticação via JWT dedicada. |
| **Employee** | Usuário do órgão responsável autenticado no Django Admin (Django staff). |
| **Organization** | Entidade responsável por uma cidade (relação 1:1 com City). |
| **State** | Estado (UF) ao qual as cidades pertencem, identificado por sigla. |
| **City** | Cidade atendida pelo aplicativo, vinculada a um State e à sua Organization. |
| **Report** | Ocorrência em si, com status, prioridade, endereço, coordenadas e relação N:N com tags. |
| **Attachment** | Fotos anexadas pelo cidadão. |
| **StatusHistory** | Linha de auditoria para cada transição de status, registrando responsável e notas. |

O fluxo de status segue **ABERTO → ANALISANDO → DEFERIDO → EM_ANDAMENTO → CONCLUÍDO** com ramificações para **INDEFERIDO** e marcação manual como **IGNORADO** quando ultrapassar 168 horas sem atualização.

## Arquitetura em camadas

```
core/
├── reports/          # Models, admin e migrações do domínio de ocorrências
├── repositories/     # Consultas SQL parametrizadas e agregações
├── services/         # Regras de negócio e transações (ex.: mudanças de status)
└── api/              # Serializers, autenticação e viewsets DRF
accounts/             # Modelos e endpoints de cadastro/autenticação
```

- **Camada de serviços** (`ReportService`) centraliza regras de transição, bloqueios (`select_for_update`), validação de fluxo e registro em `StatusHistory`.
- **Repositórios** expõem consultas SQL puras exigidas pelo projeto (elegíveis para ignorado, média de resolução, agrupamentos por bairro e série semanal).
- **API** expõe apenas endpoints necessários ao aplicativo do cidadão. Toda autenticação exige cabeçalhos `X_USER`, `X_APP`, `X_SIGNATURE` definidos no `.env`.
- **Admin Django** é utilizado exclusivamente pelo órgão público para triagem e atualização de status.

## Consultas SQL principais

1. **Relatórios elegíveis para marcação como ignorado** (`core.repositories.report_repository.get_reports_eligible_for_ignore`).
2. **Tempo médio de resolução por categoria** (`core.repositories.report_repository.get_average_resolution_time_by_category`).
3. **Abertos agrupados por bairro/prioridade** (`core.repositories.report_repository.get_open_reports_grouped_by_neighborhood`).
4. **Série temporal semanal por status** (`core.repositories.report_repository.get_weekly_series_by_status`).

A migração `0002_database_objects` ainda cria:
- Função `calculate_sla_hours` (MySQL) para calcular SLA em horas a partir de `due_at`.
- View `report_status_overview` para contagem por categoria e status.

## Configuração

1. Copie o arquivo `.env.example` para `.env` e ajuste os valores, incluindo as chaves de segurança dos cabeçalhos.
2. Instale as dependências listadas em `requirements.txt`.
3. Execute as migrações: `python manage.py migrate`.
4. Crie um superusuário administrador: `python manage.py createsuperuser`.
5. Inicie o servidor: `python manage.py runserver`.

Para recursos em tempo real, defina `CHANNEL_LAYER_BACKEND` (padrão `memory`) e, ao usar Redis, informe `CHANNEL_LAYER_REDIS_URL`. O `docker-compose.yml` já disponibiliza um serviço `redis` pronto (`redis://redis:6379/0`) para ser apontado por essas variáveis.

## Atualizações em tempo real

- **Stack**: Django Channels + Daphne expõem o projeto via ASGI, atendendo HTTP e WebSocket (mesmo host/porta).
- **Canal**: `ws://<host>/ws/reports/` envia `report.created` e `report.status_changed` sempre que ocorrências são criadas ou têm o status alterado.
- **Autenticação**: o mesmo JWT do app deve ser enviado (query `?token=<ACCESS>` ou header `Authorization: Bearer ...`). Sessões do Django Admin também funcionam automaticamente.
- **Segregação**: cidadãos escutam apenas o grupo `citizen_<id>` e funcionários entram em `organization_<id>`, garantindo isolamento por órgão.
- **Payload**: cada evento traz resumo do relatório (id, status, prioridade, `last_status_at`) e metadados do histórico para invalidar caches com segurança.

### Banco de dados

- **Produção**: defina `DB_ENGINE=mysql` e configure `MYSQL_*` para utilizar MySQL.
- **Testes/Desenvolvimento rápido**: mantenha `DB_ENGINE=sqlite` para usar SQLite em arquivo local.
- **Backup via `mysqldump`**: o container `backend` já instala o cliente MySQL (`mysqldump`). Em execuções fora do Docker, garanta que o cliente esteja no `PATH` ou defina `MYSQLDUMP_PATH` apontando para o binário. Os dumps completos enviados ao Supabase permanecem como `.sql`.
- **SSL opcional**: caso o servidor MySQL imponha certificados que não possuímos, use `MYSQL_SSL_MODE` (mapeado para `--ssl-mode` ou `--skip-ssl*` quando for `DISABLED`) e/ou `MYSQLDUMP_EXTRA_ARGS` para repassar flags específicas (`--ssl-ca`, `--skip-ssl-verify-server-cert` etc.).

## Autenticação

- **Cidadãos**: `POST /api/auth/citizens/register` e `POST /api/auth/citizens/token` retornam pares JWT personalizados (scope `citizen`).
- **Administradores**: `POST /api/auth/admins/register` cria usuários do órgão (login pelo Django Admin). Todos os endpoints de cadastro/token exigem os cabeçalhos `X_USER`, `X_APP`, `X_SIGNATURE`.

## Endpoints principais

| Método | Caminho | Descrição |
| --- | --- | --- |
| `GET` | `/api/categories/` | Lista categorias com departamento. |
| `GET` | `/api/tags/` | Lista tags disponíveis. |
| `POST` | `/api/reports/` | Cria ocorrência com tags e anexos (multipart). |
| `GET` | `/api/reports/` | Lista ocorrências do cidadão com filtros de status e categoria. |
| `GET` | `/api/reports/{id}/` | Detalhe completo da ocorrência. |
| `GET` | `/api/reports/eligibles-ignore` | Consulta relatórios elegíveis (apenas chamadas internas com cabeçalhos X-USER/X-APP/X-SIGNATURE). |
| `GET` | `/api/reports/avg-resolution/` | Média de resolução por categoria em horas. |
| `GET` | `/api/dashboard/` | Dados agregados (abertos por bairro/prioridade e série semanal).
| `POST` | `/api/dashboard/export/` | Exporta relatório de dashboard em JSON ou CSV.
| `WS` | `/ws/reports/` | WebSocket autenticado que publica `report.created` e `report.status_changed`. |

A coleção Postman (`postman/CityCare.postman_collection.json`) e o environment (`postman/CityCare.postman_environment.json`) já trazem todas as chamadas com variáveis preparadas.

## Testes automatizados

```
python manage.py test
```

Os testes cobrem o fluxo completo de status, validação de indeferimento, consulta de elegibilidade para ignorado e criação com múltiplas tags/anexos.

## Documentação adicional

- `requirements.txt`: dependências do projeto.
- `.env.example`: base para configuração de ambiente.
- Migrações incluem constraints `CHECK` para latitude/longitude, unicidade de tags/categorias e criação da função SQL e view de suporte.

## Próximos passos sugeridos

- Integrar armazenamento de mídia externo.
- Construir painel web para o órgão reaproveitando os serviços existentes.
- Jobs automáticos (cron):
  - Marcação automática como IGNORADO após 72h sem atualização (diário 02:00).
  - Backup diferencial diário (02:20) e backup completo semanal (domingo 03:00).
    - O diferencial envia apenas os registros alterados para um `.sql` incremental (sem gzip) no Supabase.
  - Gerenciar com `django-crontab`:
    - Adicionar: `python manage.py crontab add`
    - Listar: `python manage.py crontab show`
    - Remover: `python manage.py crontab remove`
