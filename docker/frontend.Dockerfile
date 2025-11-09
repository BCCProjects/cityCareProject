FROM node:20-alpine

WORKDIR /app

RUN apk add --no-cache bash git

COPY city_app/package.json city_app/package-lock.json ./
RUN npm ci

COPY city_app /app

EXPOSE 3000
EXPOSE 19000

CMD ["npm", "run", "web"]
