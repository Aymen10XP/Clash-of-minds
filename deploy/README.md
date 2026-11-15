# Clash of Minds Kubernetes deployment

This deployment packages the Ionic React frontend, Django backend, PostgreSQL,
and uploaded media storage as a Helm release for a local Minikube cluster.

## What Kubernetes runs

- `frontend` Deployment: two NGINX pods serving the compiled Ionic SPA.
- `backend` Deployment: one non-root Gunicorn container plus an unprivileged
  NGINX sidecar that serves uploaded media from a shared PVC.
- `postgres` StatefulSet: PostgreSQL 17 with a persistent 2 GiB data volume.
- Three ClusterIP Services: stable internal names for frontend, backend, and
  PostgreSQL even when pods are replaced.
- NGINX Ingress: sends `/api`, `/admin`, and `/static` to Django, `/media` to
  the media sidecar, and all other paths to the Ionic frontend.
- A Helm post-install/post-upgrade Job: waits for PostgreSQL, runs Django
  migrations, collects static files, and runs the existing seed command.

Configuration is stored in a ConfigMap. The Django key and database password
are stored in a Kubernetes Secret and supplied during installation. Readiness
and liveness probes prevent traffic from reaching unhealthy containers.

## Prerequisites and cluster

Install Docker Desktop, Minikube, Helm, and kubectl. Open a new terminal after
installation so the commands are available on `PATH`, then run:

```powershell
minikube start --driver=docker --cpus=4 --memory=6144
minikube addons enable ingress
kubectl cluster-info
```

## Build and load the images

```powershell
docker build -f server/Dockerfile -t clash-of-minds-backend:dev .
docker build -f client/Dockerfile -t clash-of-minds-frontend:dev .
minikube image load clash-of-minds-backend:dev
minikube image load clash-of-minds-frontend:dev
```

## Validate and install

```powershell
helm lint deploy/helm/clash-of-minds
helm template clash deploy/helm/clash-of-minds -f deploy/helm/clash-of-minds/values-minikube.yaml

$djangoSecret = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 50 | ForEach-Object {[char]$_})
$postgresPassword = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})

helm upgrade --install clash deploy/helm/clash-of-minds `
  --namespace clash-of-minds --create-namespace `
  -f deploy/helm/clash-of-minds/values-minikube.yaml `
  --set-string secrets.djangoSecretKey=$djangoSecret `
  --set-string secrets.postgresPassword=$postgresPassword `
  --wait --wait-for-jobs --timeout 10m
```

Enable the Minikube ingress addon and map `clash.local` to the address returned
by `minikube ip`. If direct ingress access is unavailable with the Docker
driver on Windows, forward the ingress controller and preserve host-based
routing:

```powershell
kubectl port-forward -n ingress-nginx service/ingress-nginx-controller 8080:80
```

Then open `http://clash.local:8080` after adding this hosts-file entry:

```text
127.0.0.1 clash.local
```

Alternatively, test without editing the hosts file:

```powershell
curl.exe -H "Host: clash.local" http://127.0.0.1:8080/
curl.exe -H "Host: clash.local" http://127.0.0.1:8080/api/auth/me/
```

## Verification

```powershell
kubectl get deploy,sts,pods,svc,ingress,pvc -n clash-of-minds
kubectl rollout status deployment/frontend -n clash-of-minds
kubectl rollout status deployment/backend -n clash-of-minds
kubectl rollout status statefulset/postgres -n clash-of-minds
helm test clash -n clash-of-minds
```

Expected result: frontend is `2/2`, backend is `1/1` with both containers
ready, PostgreSQL is `1/1`, both PVCs are `Bound`, and the Helm test reports
`Phase: Succeeded` with `ok`, `{"status": "ok"}`, and
`{"status": "ready"}`.

## Useful demonstrations

Kubernetes self-healing (delete one frontend pod and watch the Deployment
restore two replicas):

```powershell
kubectl get pods -n clash-of-minds -l app.kubernetes.io/name=frontend
kubectl delete pod <one-frontend-pod-name> -n clash-of-minds
kubectl rollout status deployment/frontend -n clash-of-minds
kubectl get pods -n clash-of-minds -l app.kubernetes.io/name=frontend
```

Inspect application behavior and probes:

```powershell
kubectl logs deployment/backend -n clash-of-minds -c backend
kubectl describe pod -n clash-of-minds -l app.kubernetes.io/name=backend
kubectl get events -n clash-of-minds --sort-by=.lastTimestamp
```

Upgrade after changing a template or value while keeping the generated
secrets:

```powershell
helm upgrade clash deploy/helm/clash-of-minds `
  --namespace clash-of-minds --reuse-values `
  --wait --wait-for-jobs --timeout 10m
```

Stop or remove the local environment:

```powershell
minikube stop
# minikube delete   # removes the cluster and all of its local data
```
