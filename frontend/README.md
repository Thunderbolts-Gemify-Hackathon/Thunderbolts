# Kaly Tao Frontend

App Expo (React Native) pour Kaly Tao.

## Setup

```bash
cd frontend
cp .env.example .env
npm install
npx expo start -c
```

Configure `EXPO_PUBLIC_API_URL` dans `.env` :

- simulateur / web : `http://127.0.0.1:8000`
- téléphone : `http://<IP-LAN-du-Mac>:8000`

Le backend doit tourner depuis la racine du monorepo :

```bash
cd ..
source .venv/bin/activate
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```
