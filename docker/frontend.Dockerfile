FROM node:20-alpine

WORKDIR /app

RUN apk add --no-cache bash git

COPY city_app/package.json city_app/package-lock.json ./
RUN npm i
RUN npm i expo

COPY city_app /app

EXPOSE 3000
EXPOSE 8001

CMD ["npm", "run", "web"]
