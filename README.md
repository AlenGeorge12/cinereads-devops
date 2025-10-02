# CineReads — DevOps on AWS Free Tier

Turn favorite movies into book recommendations, deployed with a clean DevOps pipeline on AWS Free Tier.

## 1) Problem & Goal
- **Problem:** Readers want book recs that match the *feel* of movies they love.
- **Goal:** Ship CineReads with a simple, reliable, cloud-based CI/CD pipeline (build → test → deploy → monitor) that two teammates can maintain.

## 2) Scope
- **Backend:** FastAPI (recommendations, /health)
- **Frontend:** Next.js (exported static via Nginx)
- **Infra:** Docker + Docker Compose on one EC2 (Free Tier)
- **CI/CD:** GitHub Actions (build, scan, push, deploy via SSH)
- **Secrets:** AWS SSM Parameter Store
- **Monitoring:** CloudWatch logs + a basic alarm

## 3) Architecture (high level)
Dev → GitHub → Actions (Build/Test/Scan) → GHCR → EC2 (Compose) → CloudWatch

## 4) Tech Stack
Git, GitHub Actions, Docker/Compose, FastAPI, Next.js, AWS EC2, SSM, CloudWatch, Trivy.

## 5) Repository Layout
- `backend/` – FastAPI app (main.py, etc.)
- `frontend/` – Next.js app
- `docker/` – Dockerfiles (backend, frontend)
- `docs/` – Abstract (PDF) + any diagrams
- `ppt/` – Presentation slides
- `.github/workflows/ci.yml` – Pipeline

## 6) Environment Variables
Create `.env` on the EC2 instance (never commit):
OPENAI_API_KEY=...
HARDCOVER_API_KEY=...
Use `aws ssm get-parameter ... --with-decryption` in deploy scripts to generate `.env`.

## 7) Local Dev (optional)
- Backend: `uvicorn main:app --reload` inside `backend/`
- Frontend: `npm run dev` inside `frontend/`

## 8) Run via Docker Compose (on EC2)
docker compose pull
docker compose up -d

## 9) Health
- Backend: `GET /health` → JSON `{ status: "healthy", ... }`

## 10) Roadmap
- R1: Repo + docs + minimal CI
- R2: Full CI/CD + security scan + logging/alarm
- Future: k3s/Kubernetes, Prometheus+Grafana, blue/green deploys
EOF
