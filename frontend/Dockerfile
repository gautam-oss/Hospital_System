# ─────────────────────────────────────────────────────────────
# REACT DOCKERFILE (Development)
# Runs the Vite dev server with hot module replacement.
# ─────────────────────────────────────────────────────────────

FROM node:20-alpine

WORKDIR /app

# Copy package files first (same caching trick as Python)
COPY package.json package-lock.json* ./
RUN npm install

COPY . .

EXPOSE 5173

# --host 0.0.0.0 makes Vite accessible from outside the container
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
