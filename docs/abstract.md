# CineReads — DevOps Mini Project (Abstract)

**Objective.** Deploy CineReads (FastAPI + Next.js) to AWS Free Tier with a simple, secure CI/CD pipeline that automates build, test, image scanning, and deployment, and provides basic monitoring.

**Problem.** Readers often struggle to find books that match the tone, themes, and narrative texture of films they love. CineReads bridges this gap using an LLM and the Hardcover API to suggest fiction books aligned to a viewer’s overall taste profile.

**Approach.** We containerize backend and frontend, store API keys in AWS Systems Manager Parameter Store, and run both services on an EC2 Free Tier instance via Docker Compose. GitHub Actions builds and scans images (Trivy), pushes to GitHub Container Registry, and deploys to EC2 over SSH. CloudWatch provides logs and a basic health alarm.

**Deliverables (Review-1).** 
- GitHub repository with README, .gitignore, abstract (PDF), and Review-1 PPT.
- Minimal CI workflow scaffold and local Dockerfiles/Compose.
- Screenshots of repo, initial pipeline run, and environment setup.

**Deliverables (Review-2).**
- Full CI/CD (build → test → scan → push → deploy), CloudWatch logs, one alarm.
- Slides showing architecture, pipeline screenshots, and results.
- Short demo: commit triggers pipeline and live update.

**Outcomes.** A low-cost, team-friendly pipeline with clear roles and artifacts that demonstrate DevOps fundamentals: version control, automation, containerization, secure secret handling, and monitoring.
