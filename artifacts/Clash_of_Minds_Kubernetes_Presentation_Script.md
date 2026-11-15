# Clash of Minds — Kubernetes Presentation Workflow

This file is our speaking script and demonstration order. It is intentionally practical: for every part, it tells us **what to show**, **which file contains it**, **what it does**, and **what to say to the professor**.

## 1. Before the presentation

Open these before the professor arrives:

1. Docker Desktop.
2. Two PowerShell terminals in the project root:

   ```powershell
   cd "D:\tekup\ing 5\ionic\Clash-of-minds"
   ```

3. The project in the code editor.
4. This presentation script.
5. A browser tab for `http://clash.local:18081`.

Start the existing environment:

```powershell
minikube start
kubectl get pods -n clash-of-minds
helm status clash -n clash-of-minds
```

In the second terminal, keep the ingress port-forward running:

```powershell
kubectl port-forward -n ingress-nginx service/ingress-nginx-controller 18081:80
```

The Windows hosts file should contain:

```text
127.0.0.1 clash.local
```

Do not rebuild or reinstall everything on presentation day unless the cluster was deleted or the application changed.

---

## 2. Opening — explain the objective

### Show

- The running Clash of Minds application.
- The repository root.

### Say

> Our project is Clash of Minds. It has an Ionic React frontend, a Django API, and a PostgreSQL database. The objective of this DevOps work was to containerize the complete application and deploy it to Kubernetes in a repeatable way. We used Docker for the application images, Minikube as our local Kubernetes cluster, and Helm to manage the complete release.

> The final deployment contains the frontend, backend, database, persistent storage, health checks, configuration, secrets, ingress routing, automated database migrations, and a Helm smoke test.

---

## 3. Explain the Docker work

### 3.1 Backend production image

### Open

[`server/Dockerfile`](../server/Dockerfile)

### Explain

- Starts from `python:3.13-slim`.
- Installs the Django dependencies from `server/requirements.txt`.
- Copies the Django project into the image.
- Collects static files during the image build.
- Creates and uses a non-root user with ID `10001`.
- Runs Django with Gunicorn on port `8000`.

### Say

> This file creates the backend production image. We do not use Django's development server inside Kubernetes. We run Gunicorn, use three workers, and run the process as a non-root user for better security.

### 3.2 Frontend production image

### Open

[`client/Dockerfile`](../client/Dockerfile)

### Explain

- Uses a multi-stage Docker build.
- The Node stage installs dependencies and builds the Ionic React application.
- The final NGINX stage contains only the compiled frontend.
- The development dependencies are not included in the runtime image.

### Say

> The frontend uses a multi-stage image. Node compiles the Ionic application, then only the generated files are copied into NGINX. This produces a smaller runtime image than keeping Node and the source code in production.

### 3.3 Frontend routing and health check

### Open

[`client/nginx.conf`](../client/nginx.conf)

### Explain

- `/healthz` returns `200 ok` for Kubernetes probes.
- `try_files` falls back to `index.html`, which allows Ionic client-side routes to work after a browser refresh.

### Say

> This NGINX configuration solves two problems. It gives Kubernetes a lightweight health endpoint, and it sends unknown browser routes back to the Ionic entry page so the single-page application can handle them.

### 3.4 Docker build context

### Open

[`/.dockerignore`](../.dockerignore)

### Say

> The Docker ignore file prevents Git data, local dependencies, build output, media files, and documentation from being copied into the image build context. This keeps builds cleaner and faster.

---

## 4. Explain the Django changes for Kubernetes

### 4.1 Health and readiness endpoints

### Open

[`server/health.py`](../server/health.py) and [`server/urls.py`](../server/urls.py)

### Explain

- `/health/` checks whether the Django process can answer requests.
- `/ready/` also executes `SELECT 1` against PostgreSQL.
- A failed readiness check removes the pod from Service traffic without immediately treating the process as dead.

### Say

> Liveness and readiness have different purposes. Liveness tells Kubernetes whether the process should be restarted. Readiness tells Kubernetes whether this pod is currently able to receive traffic. Our readiness endpoint also checks the database connection.

### 4.2 Environment-based settings

### Open

[`server/settings.py`](../server/settings.py)

### Explain

- The Django secret key and PostgreSQL password come from environment variables.
- Database host, port, name, and user are configurable.
- Allowed hosts and trusted origins are configurable for ingress.
- WhiteNoise serves collected Django static files.
- Uploaded files use `/app/media`, which is mounted to persistent storage.

### Say

> We removed infrastructure-specific values from the source code. Kubernetes injects configuration and secrets as environment variables. This lets the same image run with different settings without rebuilding it.

---

## 5. Introduce the Helm chart

### Open

[`deploy/helm/clash-of-minds/Chart.yaml`](../deploy/helm/clash-of-minds/Chart.yaml)

### Say

> Instead of applying many unrelated YAML files manually, we packaged the complete Kubernetes deployment as one Helm chart. Helm gives us one versioned release, configurable values, upgrades, history, and automated tests.

### Then open

[`deploy/helm/clash-of-minds/values.yaml`](../deploy/helm/clash-of-minds/values.yaml)

### Explain

- The common host is `clash.local`.
- Frontend replica count is `2`.
- Backend replica count is `1`.
- PostgreSQL storage is `2 GiB`.
- Uploaded media storage is `1 GiB`.
- CPU and memory requests and limits are defined.
- Image names and tags can be changed without editing templates.

### Say

> The values file is the configuration interface of the chart. For example, we can change the image tag, replica count, storage size, or resource limits without rewriting the Kubernetes templates.

### Open

[`deploy/helm/clash-of-minds/values-minikube.yaml`](../deploy/helm/clash-of-minds/values-minikube.yaml)

### Say

> This small override file contains the settings that are specific to our local Minikube environment. The images are local development images, so the pull policy is `IfNotPresent`.

---

## 6. Present each Kubernetes resource

### 6.1 ConfigMap and Secret

### Open

[`deploy/helm/clash-of-minds/templates/config.yaml`](../deploy/helm/clash-of-minds/templates/config.yaml)

### Say

> The ConfigMap stores normal application configuration, such as the host, database name, and database Service address. Sensitive values are placed in a Kubernetes Secret. We supply real secret values during installation and do not commit them to Git.

Do not display or read real secret values during the presentation.

### 6.2 Frontend Deployment and Service

### Open

[`deploy/helm/clash-of-minds/templates/frontend.yaml`](../deploy/helm/clash-of-minds/templates/frontend.yaml)

### Explain

- A Deployment maintains two frontend replicas.
- A ClusterIP Service gives the frontend a stable internal address.
- Readiness and liveness probes call `/healthz`.
- Resource requests and limits are applied.

### Say

> The frontend is stateless, so a Deployment is appropriate. Kubernetes maintains two replicas. If one pod disappears, the ReplicaSet creates a replacement. The Service keeps the same DNS name even though pod IP addresses change.

### 6.3 Backend Deployment, Service, and media storage

### Open

[`deploy/helm/clash-of-minds/templates/backend.yaml`](../deploy/helm/clash-of-minds/templates/backend.yaml)

### Explain

- The backend pod has two containers.
- The first container runs Django with Gunicorn.
- The second container is an unprivileged NGINX media server.
- Both containers share the `backend-media` PersistentVolumeClaim.
- Django writes uploaded files; the sidecar serves them.
- Probes call `/health/` and `/ready/`.
- The backend runs as a non-root user and cannot escalate privileges.

### Say

> The backend uses the sidecar pattern. Django and the media server run in the same pod and share one persistent volume. Django writes uploaded files, while NGINX serves them efficiently. The PVC keeps the uploaded files when the pod is replaced.

### 6.4 PostgreSQL StatefulSet and storage

### Open

[`deploy/helm/clash-of-minds/templates/postgres.yaml`](../deploy/helm/clash-of-minds/templates/postgres.yaml)

### Explain

- PostgreSQL uses a StatefulSet instead of a Deployment.
- It receives a predictable identity and a dedicated volume claim.
- `pg_isready` is used for liveness and readiness checks.
- The PostgreSQL Service gives Django the stable hostname `postgres`.

### Say

> PostgreSQL is stateful, so it uses a StatefulSet. The database pod can be recreated and remount the existing PersistentVolumeClaim. This is why deleting the database pod does not delete the database data.

### 6.5 Ingress routing

### Open

[`deploy/helm/clash-of-minds/templates/ingress.yaml`](../deploy/helm/clash-of-minds/templates/ingress.yaml)

### Explain

| Request path | Destination |
|---|---|
| `/` and frontend routes | Frontend Service |
| `/api` | Django backend |
| `/admin` | Django backend |
| `/static` | Django backend |
| `/media` | Backend media sidecar |

### Say

> Ingress is the single entry point. The user sees one host, `clash.local`, while NGINX Ingress selects the correct internal Service according to the URL path.

### 6.6 Automated migrations and seed data

### Open

[`deploy/helm/clash-of-minds/templates/migrate-job.yaml`](../deploy/helm/clash-of-minds/templates/migrate-job.yaml)

### Explain

- It is a Helm post-install and post-upgrade hook.
- An init container waits for PostgreSQL.
- The job runs Django migrations and `seed_quiz`.
- Helm waits for the job before reporting success.

### Say

> Database initialization is automated. On every installation or upgrade, the job waits for PostgreSQL, applies migrations, and runs our seed command. This avoids manually entering the backend container to prepare the database.

### 6.7 Helm smoke test

### Open

[`deploy/helm/clash-of-minds/templates/tests/test-connection.yaml`](../deploy/helm/clash-of-minds/templates/tests/test-connection.yaml)

### Say

> The chart contains a test pod. It checks the frontend health endpoint, the backend liveness endpoint, and the database-backed readiness endpoint from inside the cluster.

---

## 7. Explain how the deployment is launched

Tell the professor that these are the full installation steps. They do not all need to be executed live if the cluster is already prepared.

### Step 1 — start Kubernetes

```powershell
minikube start --driver=docker --cpus=4 --memory=6144
minikube addons enable ingress
kubectl cluster-info
```

### Say

> Minikube creates a local Kubernetes cluster using Docker Desktop. The ingress add-on installs the NGINX ingress controller.

### Step 2 — build the application images

```powershell
docker build -f server/Dockerfile -t clash-of-minds-backend:dev .
docker build -f client/Dockerfile -t clash-of-minds-frontend:dev .
```

### Step 3 — load the images into Minikube

```powershell
minikube image load clash-of-minds-backend:dev
minikube image load clash-of-minds-frontend:dev
```

### Say

> The images currently exist locally instead of in an external registry, so we load them into the Minikube node before installation.

### Step 4 — validate the Helm chart

```powershell
helm lint deploy/helm/clash-of-minds
helm template clash deploy/helm/clash-of-minds `
  -f deploy/helm/clash-of-minds/values-minikube.yaml
```

### Say

> Lint checks the chart structure. Template renders the generated Kubernetes YAML locally, which lets us detect invalid values before changing the cluster.

### Step 5 — generate secrets and install

```powershell
$djangoSecret = ([guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N'))
$postgresPassword = [guid]::NewGuid().ToString('N')

helm upgrade --install clash deploy/helm/clash-of-minds `
  --namespace clash-of-minds --create-namespace `
  -f deploy/helm/clash-of-minds/values-minikube.yaml `
  --set-string "secrets.djangoSecretKey=$djangoSecret" `
  --set-string "secrets.postgresPassword=$postgresPassword" `
  --wait --wait-for-jobs --timeout 10m
```

### Say

> We use `upgrade --install`, so the same command can create a new release or update an existing release. The wait flags mean Helm reports success only when the workloads and migration job are ready.

---

## 8. Show the running result

Run:

```powershell
kubectl get deployments,statefulsets,pods,services,ingress,pvc -n clash-of-minds
helm status clash -n clash-of-minds
```

### Point out

- Frontend Deployment: `2/2` replicas ready.
- Backend pod: `2/2` containers ready.
- PostgreSQL StatefulSet: `1/1` ready.
- Three internal Services: frontend, backend, and PostgreSQL.
- Ingress: created for `clash.local`.
- Media PVC: `Bound`, size `1 GiB`.
- Database PVC: `Bound`, size `2 GiB`.

### Say

> This output proves that Kubernetes reached the desired state. Deployments and the StatefulSet are ready, both persistent volumes are bound, and the Services and Ingress are available.

Open `http://clash.local:18081` and quickly demonstrate that the user-facing application loads.

Optional route checks:

```powershell
curl.exe -H "Host: clash.local" http://127.0.0.1:18081/
curl.exe -H "Host: clash.local" http://127.0.0.1:18081/api/auth/me/
curl.exe -I -H "Host: clash.local" http://127.0.0.1:18081/admin/
```

Expected HTTP results:

- Frontend: `200`.
- API: `200`.
- Django admin: `302` redirect to login.

---

## 9. Live demonstration 1 — Helm test

Run:

```powershell
helm test clash -n clash-of-minds --logs
```

### Say

> This is an automated smoke test that runs inside Kubernetes. It verifies the frontend, Django process, and database-backed readiness endpoint. `Phase: Succeeded` means the main internal communication paths work.

---

## 10. Live demonstration 2 — Kubernetes self-healing

First list the frontend pods:

```powershell
kubectl get pods -n clash-of-minds -l app.kubernetes.io/name=frontend
```

Copy one pod name and delete it:

```powershell
kubectl delete pod <frontend-pod-name> -n clash-of-minds
kubectl rollout status deployment/frontend -n clash-of-minds
kubectl get pods -n clash-of-minds -l app.kubernetes.io/name=frontend
```

### Say

> We intentionally deleted one frontend pod. The Deployment still requires two replicas, so the ReplicaSet detected the difference and created a replacement automatically. The new pod name proves that Kubernetes performed self-healing.

Do not delete both frontend pods during the presentation.

---

## 11. Mention the validation work

### Say

> We did not stop after writing YAML files. We validated the application and the deployment. The Django test suite passed 59 tests, the frontend Vitest suite passed 19 tests, ESLint passed, the Ionic production build succeeded, both Docker images built successfully, and Helm lint passed.

> After deployment, we validated the Helm test, ingress routes, frontend self-healing, and PostgreSQL persistence. A database validation row remained after the PostgreSQL pod was replaced, which proves that the database volume was remounted correctly. The temporary validation data was removed afterwards.

---

## 12. Likely questions and short answers

### Why use a Deployment for the frontend and backend?

They are application workloads. Deployments manage replicas, rolling updates, and replacement pods.

### Why use a StatefulSet for PostgreSQL?

PostgreSQL needs stable identity and persistent storage. Its PVC survives pod replacement.

### Why do we need Services?

Pod IP addresses can change. Services provide stable internal DNS names and route traffic to ready pods.

### Why use Ingress?

Ingress exposes one host and routes different URL paths to the correct internal Services.

### Why use Helm?

Helm packages the templates and values as one repeatable release. It supports installation, upgrades, testing, history, and rollback.

### What is the difference between liveness and readiness?

Liveness decides whether Kubernetes should restart a container. Readiness decides whether a pod may receive traffic.

### Where are the secrets?

The Helm chart creates a Kubernetes Secret from values supplied during installation. Real values are not committed to Git.

### Is this production-ready?

It is a complete local Kubernetes implementation for the course. A real production deployment would additionally use a container registry, TLS, stronger secret management, monitoring, backups, multiple nodes, and usually a managed or highly available database.

### What would we add next?

CI/CD, a container registry, HTTPS, monitoring with Prometheus and Grafana, centralized logs, database backups, and cloud Kubernetes deployment.

---

## 13. Closing statement

### Say

> We reached the Kubernetes objective because the complete Clash of Minds application is deployed as one repeatable Helm release. The workloads become ready, ingress routes the application correctly, Kubernetes restores a deleted pod, and PostgreSQL data survives pod replacement. This implementation gives us a tested foundation for future CI/CD, monitoring, security, and cloud deployment work.

---

## 14. Emergency presentation checklist

If something fails during the presentation, stay on the current step and use these commands:

```powershell
kubectl get all -n clash-of-minds
kubectl get ingress,pvc -n clash-of-minds
kubectl get events -n clash-of-minds --sort-by=.lastTimestamp
kubectl describe pod <pod-name> -n clash-of-minds
kubectl logs <pod-name> -n clash-of-minds -c <container-name>
helm status clash -n clash-of-minds
helm history clash -n clash-of-minds
```

Common quick checks:

- Browser cannot open the application: verify the hosts entry and ingress port-forward.
- `ImagePullBackOff`: verify both local images were loaded into Minikube.
- Backend is not ready: inspect the backend pod, PostgreSQL pod, ConfigMap, and Secret names.
- Pod is pending: inspect PVC status and available Minikube CPU and memory.
- API returns `404`: verify the request uses the `clash.local` Host header and inspect the Ingress paths.

If the live application fails completely, continue using the code files and the validated-results section. Explain what each resource does and show the previously generated presentation guide rather than spending the entire presentation debugging.
