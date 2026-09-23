# AI Job Matching System

A full-stack AI job matching platform with:

- BERT-powered resume and job embeddings
- Siamese similarity learning on `Resume.csv`
- Skill extraction and overlap scoring
- Internship-aware recommendation logic
- Real-time FastAPI recommendation API
- React admin dashboard
- Docker + Render/AWS deployment scaffolding

## Project structure

```text
gcs-ai-matching-system/
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── schemas.py
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── nlp_processor.py
│   │   ├── bert_siamese.py
│   │   ├── ranker.py
│   │   └── training.py
│   ├── data/
│   │   ├── Resume.csv            # put your dataset here
│   │   └── sample_jobs.json
│   ├── models/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── vite.config.js
├── deploy/
│   ├── aws-ecs-task-def.json
│   └── render.yaml
├── docker-compose.yml
└── README.md
```

## Resume.csv format

The training loader is tolerant to common column names. It looks for a resume text column and a class/category column.

Supported resume columns:
- `Resume`
- `resume`
- `resume_text`
- `text`
- `content`

Supported label columns:
- `Category`
- `category`
- `job_category`
- `domain`
- `label`

Example:

```csv
Category,Resume
Data Science,"Python, pandas, machine learning, SQL, data analysis..."
Web Designing,"HTML, CSS, JavaScript, React, UI/UX..."
DevOps,"Docker, Kubernetes, AWS, CI/CD, Linux..."
```

## Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## Train the Siamese model

From project root:

```bash
python -m backend.engine.training --csv backend/data/Resume.csv --epochs 3 --batch-size 16
```

Or via API:

```bash
curl -X POST http://localhost:8000/api/v1/train \
  -H "Content-Type: application/json" \
  -d '{"csv_path":"backend/data/Resume.csv","epochs":3,"batch_size":16}'
```

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Set the API URL with:

```bash
VITE_API_URL=http://localhost:8000/api/v1
```

## Docker

```bash
docker compose up --build
```

Backend: `http://localhost:8000/docs`
Frontend: `http://localhost:3000`

## API examples

### Match jobs

```bash
curl -X POST http://localhost:8000/api/v1/match \
  -H "Content-Type: application/json" \
  -d @payload.json
```

Example payload:

```json
{
  "candidate_resume": "Computer science student with Python, FastAPI, React, Docker and SQL.",
  "jobs": [
    {
      "title": "AI/ML Intern",
      "company": "Acme AI",
      "description": "Work on Python, NLP, embeddings, APIs and data pipelines.",
      "job_type": "internship"
    },
    {
      "title": "Senior DevOps Engineer",
      "company": "CloudCorp",
      "description": "Own AWS, Kubernetes, Terraform and SRE platform operations.",
      "job_type": "full-time"
    }
  ],
  "top_k": 5
}
```

### Extract skills

```bash
curl -X POST http://localhost:8000/api/v1/extract-skills \
  -H "Content-Type: application/json" \
  -d '{"text":"Python, FastAPI, React, Docker, AWS and PostgreSQL"}'
```

## How the ranking works

Each recommendation score combines:

- **Semantic similarity** from the Siamese network on top of BERT embeddings
- **Skill overlap** between extracted candidate and job skills
- **Internship/entry-level alignment** for students and early-career applicants
- **Minor penalties** for obvious seniority mismatches

Default weighting:

- Semantic similarity: `65%`
- Skill match: `25%`
- Career-stage fit: `10%`

## Deployment

### Render

- Use `deploy/render.yaml`
- Create two services:
  - backend web service from `backend/Dockerfile`
  - frontend static or Docker service from `frontend/`

### AWS

- Use the included ECS task definition as a starting point
- Build and push the backend image to ECR
- Attach an ALB for public API access
- Serve the frontend via S3 + CloudFront or containerize it separately

## Notes

- The model will work out of the box with the pretrained embedding backbone.
- Training improves domain adaptation when `Resume.csv` has clean categories.
- This starter is production-oriented, but you should still add auth, persistence, logging, and monitoring before going live.
