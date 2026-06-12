# ── NetWatch Frontend ──────────────────────────
FROM node:22-alpine AS base

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm ci --prefer-offline --legacy-peer-deps 2>/dev/null || npm install --legacy-peer-deps

# Copy source
COPY . .

# Expose port
EXPOSE 3000

# Development mode with hot-reload
CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0"]
