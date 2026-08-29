FROM node:22-bookworm-slim
WORKDIR /app
ENV NODE_ENV=production
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN mkdir -p .grok && printf '%s\n' '{"VITE_AUTH_ENABLED":"false","deploy":{"database":true}}' > .grok/app-env.json
RUN npm run build
EXPOSE 7860
CMD ["node", "scripts/with-app-env.mjs", "vite", "preview", "--host", "0.0.0.0", "--port", "7860"]
