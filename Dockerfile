FROM node:22-alpine AS web-build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY index.html vite.config.js ./
COPY src ./src
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY scripts ./scripts
COPY data/nse_daily ./data/nse_daily
COPY --from=web-build /app/dist ./dist
ENV VIBEBT_HOST=0.0.0.0
CMD ["python", "scripts/kite_bridge.py"]
