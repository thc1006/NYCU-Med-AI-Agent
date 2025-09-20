# 多階段構建 Dockerfile
# 階段 1: 構建前端
FROM node:18-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --only=production
COPY frontend/ ./
RUN npm run build

# 階段 2: Python 後端
FROM python:3.11-slim AS backend
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 複製並安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製後端程式碼
COPY app/ ./app/

# 複製前端構建結果
COPY --from=frontend-build /app/frontend/build ./frontend/build

# 設定環境變數
ENV PYTHONPATH=/app
ENV ENVIRONMENT=production

# 暴露端口
EXPOSE 8000

# 健康檢查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/v1/monitoring/health || exit 1

# 啟動命令
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]