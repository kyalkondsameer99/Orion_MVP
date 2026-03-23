# Infrastructure

Production-style infra (Terraform, cloud DB, secrets manager) can live here. For local MVP, orchestration is **`docker-compose.yml`** at the repository root.

- **Postgres** — primary database  
- **Redis** — RQ job queue  
- **Backend / frontend** — see root `README.md`  

No additional files are required to run the MVP locally.
