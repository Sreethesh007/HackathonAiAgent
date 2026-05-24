# ── Stage 1: Build ──────────────────────────────────────────────────────────
FROM node:20-alpine AS builder
WORKDIR /app

# Install dependencies first (layer cache)
COPY package*.json ./
RUN npm ci --omit=optional

# Copy source and build
COPY . .
RUN npx ng build --configuration production --output-path dist/

# ── Stage 2: Serve via Nginx ─────────────────────────────────────────────────
FROM nginx:1.27-alpine AS runtime

# Copy compiled app
COPY --from=builder /app/dist/ /usr/share/nginx/html/

# Copy Nginx config (SPA routing + API proxy)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -qO- http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
