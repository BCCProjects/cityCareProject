## CityCare Mobile (`city_app`)

Aplicativo React Native + Expo focado nas interações do cidadão com a plataforma CityCare. Toda funcionalidade exposta pela API para usuários finais está coberta: autenticação, cadastro, consultas de dados de apoio, abertura de ocorrências e acompanhamento completo.

### Principais recursos
- Cadastro e login de cidadãos com armazenamento seguro dos tokens JWT.
- Consulta de estados, cidades, departamentos, categorias e tags diretamente do backend.
- Lista de ocorrências com filtros, detalhamento (incluindo anexos) e indicadores de status/priority.
- Formulário completo para abertura de novas ocorrências com seleção de tags e upload de até 5 imagens.
- Área de perfil trazendo os dados básicos do cidadão e ação para encerrar sessão.
- Arquitetura componentizada em `src/` para facilitar evolução visual e de funcionalidades.

### Variáveis de ambiente
As variáveis acessíveis no app ficam em `city_app/.env` (já versionado para o ambiente local). Utilize sempre o prefixo `EXPO_PUBLIC_`.

```ini
EXPO_PUBLIC_API_BASE_URL=http://backend:8000/api
EXPO_PUBLIC_X_APP=mycitycareapp
EXPO_PUBLIC_X_USER=mycitycareuser
EXPO_PUBLIC_X_SIGNATURE=secret-signature
EXPO_PUBLIC_MAX_ATTACHMENTS=5
EXPO_PUBLIC_GOOGLE_MAPS_SECRET_KEY=your-google-maps-sdk-key
```

- Ajuste `EXPO_PUBLIC_API_BASE_URL` para o endereço apropriado (`http://127.0.0.1:8000/api` fora de containers ou `http://backend:8000/api` via Docker).
- Os cabeçalhos `X-APP`, `X-USER` e `X-SIGNATURE` devem permanecer alinhados aos definidos em `city_care/.env`.
- `EXPO_PUBLIC_GOOGLE_MAPS_SECRET_KEY` libera o autocomplete do Google Places e o provider Google Maps no seletor de localização do formulário de ocorrência.

### Localização assistida
- A tela de nova ocorrência agora traz um seletor visual com mapa, autocomplete do Google Places e botão para usar a localização atual (via `expo-location`).
- Basta tocar no mapa ou escolher um endereço para que latitude e longitude sejam preenchidos automaticamente nos dados enviados ao backend.
- Para iOS/Android nativos é recomendado definir `expo.ios.config.googleMapsApiKey` e `expo.android.config.googleMaps.apiKey` no `app.json` antes de gerar builds, reutilizando `EXPO_PUBLIC_GOOGLE_MAPS_SECRET_KEY`.

### Executando localmente
```bash
cd city_app
npm install
npm run web          # roda em http://localhost:8081
# ou
npm start            # abre o menu interativo do Expo
```

O layout é responsivo e pode ser aberto tanto no Expo Go (Android/iOS) quanto no navegador.

### Docker / Monorepo
Na raiz do repositório há um `docker-compose.yml` que inicia MySQL, backend Django e este frontend:

```bash
docker compose up --build
```

Serviços expostos:
- Expo Web: http://localhost:8081
- Django API: http://localhost:8000
- MySQL: localhost:3306

O código das pastas `city_care/` e `city_app/` é montado como volume, permitindo hot reload durante o desenvolvimento.

### Estrutura relevante
- `app/`: rotas com Expo Router, separadas em grupos `(auth)` e `(app)` (com tabs).
- `src/components`: componentes reutilizáveis (inputs, botões, feedbacks, etc.).
- `src/features`: lógica de domínio (auth, referências, reports) organizada por contexto.
- `src/lib`: clients compartilhados (axios com headers padrão, react-query).
- `src/config/env.ts`: leitura centralizada das variáveis públicas do Expo.

### Próximos passos sugeridos
1. Implementar histórico de status da ocorrência quando o backend expor o endpoint correspondente.
2. Adicionar testes E2E (Detox ou Playwright) para fluxos críticos de login e abertura de ocorrência.
3. Disponibilizar opções de tema (dark/brand) aproveitando a componentização existente.
