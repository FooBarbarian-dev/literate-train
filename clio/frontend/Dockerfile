FROM node:22-alpine
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY index.html vite.config.js ./
COPY src/ ./src/
EXPOSE 3000
# NOTE (PoC): Running Vite dev server instead of a production build.
# The dev server's built-in proxy (vite.config.js) routes /api -> backend
# and /relation-service -> relation-service, so no separate reverse proxy
# (nginx) is needed. For production, build the app and serve behind nginx
# with proper TLS.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
