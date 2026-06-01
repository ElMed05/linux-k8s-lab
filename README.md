# Linux Kubernetes Lab mit Ansible, Helm, Ingress, TLS, Gateway API und Data Platform

Dieses Projekt baut ein praxisnahes Kubernetes-Lab auf Basis von Ubuntu Server VMs in VMware Workstation auf.

Der Fokus liegt nicht nur auf einer Kubernetes-Installation, sondern auf einem nachvollziehbaren Plattform-Betriebsmodell: Linux-Server werden automatisiert vorbereitet, ein Multi-Node-Kubernetes-Cluster wird mit Ansible aufgebaut, Plattform-Komponenten werden über Rollen verwaltet und darauf läuft inzwischen eine kleine Data Intelligence Platform.

Das Lab ist damit eine kompakte **Platform Engineering Foundation** mit Richtung **Data Platform, Lakehouse, Data Processing und MLOps**.

---

## Kurzüberblick

Aktuell umfasst das Projekt:

```text
VMware Workstation
├── k8s-master-01
│   └── Kubernetes Control Plane
│
└── k8s-worker-01
    └── Worker Node

Plattform-Komponenten
├── containerd
├── kubeadm / kubelet / kubectl
├── Flannel CNI
├── Helm
├── ingress-nginx
├── cert-manager
├── Gateway API
└── NGINX Gateway Fabric

Data Platform
├── data-generator CronJob
├── data-api FastAPI Service
├── PostgreSQL mit PersistentVolume
└── Metabase Dashboard
```

---

## Architekturübersicht

```text
Control-Rechner
└── Ansible Projekt: linux-k8s-lab
    ├── Inventory
    ├── Playbooks
    ├── Ansible Rollen
    ├── Ansible Vault
    ├── versionierte Kubernetes-Manifeste
    ├── Data Platform App-Code
    └── SSH-Key Zugriff
             │
             │ verwaltet per SSH/Ansible
             ▼
VMware Workstation
├── k8s-master-01
│   ├── Ubuntu Server 24.04 LTS
│   ├── Kubernetes Control Plane
│   │   ├── kube-apiserver
│   │   ├── kube-scheduler
│   │   ├── kube-controller-manager
│   │   └── etcd
│   ├── kubelet
│   ├── kube-proxy
│   ├── containerd
│   ├── Flannel CNI
│   ├── kubectl
│   └── Helm
│
└── k8s-worker-01
    ├── Ubuntu Server 24.04 LTS
    ├── kubelet
    ├── kube-proxy
    ├── containerd
    ├── Flannel CNI
    ├── Gateway/Data-Plane Pods
    ├── Data API
    ├── PostgreSQL
    └── Metabase
```

---

## Data Platform Architektur

Die Data Platform bildet eine kleine, aber realistische Pipeline ab:

```text
Kubernetes CronJob
        │
        ▼
data-generator
        │
        │ sendet JSON Events
        ▼
data-api FastAPI
        │
        │ schreibt strukturierte Daten
        ▼
PostgreSQL
        │
        │ wird als Datenquelle genutzt von
        ▼
Metabase Dashboard
```

### Datenfluss

```text
data-generator
→ POST /services
→ POST /metrics
→ POST /incidents
→ data-api
→ PostgreSQL
→ Metabase Dashboard
```

### Data Platform Komponenten

| Komponente | Zweck |
|---|---|
| `data-generator` | Kubernetes CronJob, erzeugt regelmäßig Service-Metriken und Incidents |
| `data-api` | FastAPI Ingestion API für Betriebsdaten |
| `data-processing` | Kubernetes CronJob, berechnet Service-Health-Kennzahlen aus Metriken und Incidents |
| `postgres` | Persistente Speicherung der Data Platform Daten |
| `metabase` | Dashboard- und BI-Oberfläche |
| `ghcr-secret` | Kubernetes Image Pull Secret für private GHCR Images |
| `postgres-local-pv` | Lokales PersistentVolume für PostgreSQL |
| `data-api-route` | Gateway API Route für die Data API |
| `metabase-route` | Gateway API Route für das Dashboard |

### Data Platform Datenmodell

Die API erstellt beim Start automatisch diese Tabellen:

```text
services
service_metrics
incidents
service_health_summary
```

Beispielhafte Inhalte:

```text
services
├── checkout-api
├── payment-api
├── inventory-service
├── user-service
└── notification-service

service_metrics
├── cpu_usage
├── memory_usage
├── response_time_ms
├── request_count
└── error_rate

incidents
├── severity
├── incident_type
├── duration_minutes
└── resolved

service_health_summary
├── avg_cpu_usage
├── avg_memory_usage
├── avg_response_time_ms
├── avg_error_rate
├── total_requests
├── incident_count
├── health_score
└── calculated_at
```

### Data Platform Routing

```text
api.data.local:31977
→ NGINX Gateway Fabric
→ Gateway demo-gateway
→ HTTPRoute data-api-route
→ Service data-api
→ FastAPI Pod

dashboard.data.local:31977
→ NGINX Gateway Fabric
→ Gateway demo-gateway
→ HTTPRoute metabase-route
→ Service metabase
→ Metabase Pod
```

---

## Networking-Architektur

Die Demo-App und die Data Platform werden über zwei unterschiedliche Kubernetes-Networking-Modelle veröffentlicht:

```text
1. Klassisch über ingress-nginx und Ingress
2. Modern über Gateway API mit NGINX Gateway Fabric
```

### Zugriff über Ingress

```text
Browser / curl
→ demo.local:30520 / 32685
→ ingress-nginx-controller NodePort
→ Ingress Rule für demo.local
→ demo-nginx ClusterIP Service
→ demo-nginx Pod
```

Aktuelle Ingress-Zugriffspfade:

```text
HTTP:
http://demo.local:30520

HTTPS:
https://demo.local:32685
```

Da aktuell ein Self-Signed-Zertifikat genutzt wird, zeigt der Browser bei HTTPS eine Zertifikatswarnung.

### Zugriff über Gateway API

```text
Browser / curl
→ gateway.demo.local:31977
→ demo-gateway-nginx NodePort
→ Gateway demo-gateway
→ HTTPRoute demo-nginx-route
→ demo-nginx ClusterIP Service
→ demo-nginx Pod
```

Zusätzlich routet derselbe Gateway auch die Data Platform:

```text
api.data.local:31977
dashboard.data.local:31977
```

Wichtig: Der Gateway-Service nutzt aktuell `externalTrafficPolicy: Local`. Deshalb funktioniert der NodePort-Zugriff über den Worker-Node, auf dem der Gateway-Pod läuft:

```text
k8s-worker-01 / 192.168.1.16
```

---

## Aktueller Stand

- Ubuntu Server VMs in VMware Workstation
- Multi-Node Kubernetes Cluster
- Control Plane Node: `k8s-master-01`
- Worker Node: `k8s-worker-01`
- SSH-Key-basierter Zugriff
- Ansible Inventory und Playbooks
- Ansible Vault für sudo-Zugangsdaten und GHCR Token
- Zentrales `site.yml` Playbook für den Cluster-Aufbau
- Ansible-Rollenstruktur für wiederverwendbare Automatisierung
- Idempotente Playbooks: erneuter Lauf endet im Zielzustand mit `changed=0`
- Kubernetes-Manifeste versioniert im Repository
- containerd als Container Runtime
- Kubernetes v1.36 mit kubeadm
- Flannel als CNI
- Helm installiert
- Demo-App `nginx` per Helm deployed
- ingress-nginx als Ingress Controller
- cert-manager installiert
- Self-Signed TLS-Zertifikat für `demo.local`
- Gateway API CRDs installiert
- NGINX Gateway Fabric als Gateway API Controller installiert
- GatewayClass `nginx` accepted
- Gateway `demo-gateway` programmed
- HTTPRoute `demo-nginx-route` für `gateway.demo.local`
- Data Platform Namespace `data-platform`
- PostgreSQL mit lokalem PersistentVolume
- FastAPI Data API als eigenes Container Image aus GHCR
- Data Generator CronJob als eigenes Container Image aus GHCR
- Data Processing CronJob als eigenes Container Image aus GHCR
- Processing Layer berechnet `service_health_summary` aus Metriken und Incidents
- Verarbeitete Summary-Daten werden zusätzlich in MinIO `processed/` gespeichert
- Metabase Dashboard für Data Platform Daten
- Gateway API Routes für `api.data.local` und `dashboard.data.local`
- Verify-Playbook prüft Kubernetes, Gateway API und Data Platform Health
- Worker-Join-Playbook ist idempotent
- kubeadm Join Tokens werden nur erzeugt, wenn Worker noch nicht gejoint sind

---

## Serverübersicht

| Hostname | Rolle | IP | Betriebssystem | Runtime |
|---|---|---|---|---|
| `k8s-master-01` | Control Plane | `192.168.1.15` | Ubuntu Server 24.04 LTS | containerd |
| `k8s-worker-01` | Worker Node | `192.168.1.16` | Ubuntu Server 24.04 LTS | containerd |

---

## Kubernetes-Komponenten

### Control Plane auf `k8s-master-01`

```text
kube-apiserver
kube-scheduler
kube-controller-manager
etcd
```

### Node-Komponenten auf beiden Nodes

```text
kubelet
kube-proxy
containerd
Flannel CNI
```

### Plattform-Komponenten

```text
Helm
ingress-nginx
cert-manager
Gateway API
NGINX Gateway Fabric
```

### Data Platform Komponenten

```text
PostgreSQL
FastAPI data-api
data-generator CronJob
Metabase
GHCR imagePullSecret
Local PersistentVolume
Gateway API HTTPRoutes
```

---

## Projektstruktur

```text
linux-k8s-lab/
├── ansible.cfg
├── README.md
├── inventories/
│   └── lab/
│       ├── hosts.ini
│       ├── group_vars/
│       │   └── all/
│       │       └── vault-ghcr.yml
│       └── host_vars/
│           ├── k8s-master-01/
│           │   └── vault.yml
│           └── k8s-worker-01/
│               └── vault.yml
├── apps/
│   └── data-platform/
│       ├── data-api/
│       │   ├── Dockerfile
│       │   ├── requirements.txt
│       │   └── app/
│       │       ├── __init__.py
│       │       ├── database.py
│       │       ├── main.py
│       │       └── models.py
│       ├── data-generator/
│       │   ├── Dockerfile
│       │   ├── requirements.txt
│       │   └── generator.py
│       ├── data-processing/
│       │   ├── Dockerfile
│       │   ├── requirements.txt
│       │   └── processor.py
│       ├── k8s/
│       │   ├── namespace.yaml
│       │   ├── postgres-secret.yaml
│       │   ├── postgres-pv.yaml
│       │   ├── postgres-pvc.yaml
│       │   ├── postgres-deployment.yaml
│       │   ├── postgres-service.yaml
│       │   ├── data-api-deployment.yaml
│       │   ├── data-api-service.yaml
│       │   ├── data-api-httproute.yaml
│       │   ├── data-generator-cronjob.yaml
│       │   ├── data-processing-cronjob.yaml
│       │   ├── metabase-db-init-job.yaml
│       │   ├── metabase-deployment.yaml
│       │   ├── metabase-service.yaml
│       │   └── metabase-httproute.yaml
│       └── docs/
├── manifests/
│   ├── cert-manager/
│   │   ├── demo-certificate.yml
│   │   └── selfsigned-clusterissuer.yml
│   ├── ingress/
│   │   └── demo-ingress.yml
│   └── gateway-api/
│       ├── gateway.yml
│       └── httproute.yml
├── playbooks/
│   ├── site.yml
│   ├── 00-ping.yml
│   ├── 01-bootstrap.yml
│   ├── 02-base-linux.yml
│   ├── 03-container-runtime.yml
│   ├── 04-kubernetes-packages.yml
│   ├── 05-init-control-plane.yml
│   ├── 06-verify-cluster.yml
│   ├── 07-install-helm.yml
│   ├── 08-deploy-test-app.yml
│   ├── 09-join-workers.yml
│   ├── 10-install-ingress-nginx.yml
│   ├── 11-create-demo-ingress.yml
│   ├── 12-install-cert-manager.yml
│   ├── 13-create-demo-tls.yml
│   ├── 14-install-gateway-api.yml
│   └── 15-deploy-data-platform.yml
├── roles/
│   ├── base_linux/
│   ├── cert_manager/
│   ├── containerd/
│   ├── data_platform/
│   ├── demo_app/
│   ├── demo_ingress/
│   ├── demo_tls/
│   ├── gateway_api/
│   ├── helm/
│   ├── ingress_nginx/
│   ├── kubernetes_common/
│   ├── kubernetes_control_plane/
│   └── kubernetes_worker/
└── docs/
```

---

## Rollenstruktur

Die Automatisierung ist in wiederverwendbare Ansible-Rollen aufgeteilt.

```text
roles/
├── base_linux/
│   └── Linux-Basiskonfiguration, Pakete, Hostname, Timezone, Swap
├── containerd/
│   └── containerd Runtime, Kernel-Module, sysctl, Cgroup-Konfiguration
├── kubernetes_common/
│   └── Kubernetes Repository, kubeadm, kubelet, kubectl, Package Hold
├── kubernetes_control_plane/
│   └── kubeadm init, kubeconfig, Flannel CNI, Control-Plane-Konfiguration
├── kubernetes_worker/
│   └── Worker-Join-Status, sicherer kubeadm Join, Token-Vermeidung
├── helm/
│   └── Helm Installation und Versionsprüfung
├── demo_app/
│   └── Demo-App Deployment per Helm als ClusterIP Service
├── ingress_nginx/
│   └── ingress-nginx Installation per Helm als NodePort Controller
├── cert_manager/
│   └── cert-manager Installation per Helm inklusive CRDs
├── demo_ingress/
│   └── Demo Ingress Resource für demo.local
├── demo_tls/
│   └── SelfSigned ClusterIssuer, Certificate und TLS Binding
├── gateway_api/
│   └── Gateway API CRDs, NGINX Gateway Fabric, Gateway und HTTPRoute
└── data_platform/
    └── PostgreSQL, Data API, CronJob Generator, Metabase und Gateway Routes
```

---

## Ansible Inventory

Beispiel:

```ini
[k8s_control_plane]
k8s-master-01 ansible_host=192.168.1.15 ansible_user=devops ansible_python_interpreter=/usr/bin/python3

[k8s_workers]
k8s-worker-01 ansible_host=192.168.1.16 ansible_user=devops ansible_python_interpreter=/usr/bin/python3

[k8s_cluster:children]
k8s_control_plane
k8s_workers
```

---

## Ansible Vault

Sudo-Passwörter und GHCR-Zugangsdaten werden nicht im Klartext im Repository gespeichert, sondern über Ansible Vault verschlüsselt.

Beispielstruktur:

```text
inventories/lab/host_vars/k8s-master-01/vault.yml
inventories/lab/host_vars/k8s-worker-01/vault.yml
inventories/lab/group_vars/all/vault-ghcr.yml
```

GHCR-Zugangsdaten vor Verschlüsselung:

```yaml
---
ghcr_username: "GITHUB_USERNAME"
ghcr_token: "GITHUB_TOKEN_WITH_READ_PACKAGES"
```

Ausführen mit Vault:

```bash
ansible-playbook playbooks/06-verify-cluster.yml --ask-vault-pass
```

---

## Playbook-Reihenfolge

Der komplette Cluster-Aufbau kann über ein zentrales Playbook ausgeführt werden:

```bash
ansible-playbook playbooks/site.yml --ask-vault-pass
```

Einzelne Playbooks können separat ausgeführt werden.

```bash
ansible-playbook playbooks/00-ping.yml
ansible-playbook playbooks/01-bootstrap.yml --ask-vault-pass
ansible-playbook playbooks/02-base-linux.yml --ask-vault-pass
ansible-playbook playbooks/03-container-runtime.yml --ask-vault-pass
ansible-playbook playbooks/04-kubernetes-packages.yml --ask-vault-pass
ansible-playbook playbooks/05-init-control-plane.yml --ask-vault-pass
ansible-playbook playbooks/07-install-helm.yml --ask-vault-pass
ansible-playbook playbooks/09-join-workers.yml --ask-vault-pass
ansible-playbook playbooks/08-deploy-test-app.yml --ask-vault-pass
ansible-playbook playbooks/10-install-ingress-nginx.yml --ask-vault-pass
ansible-playbook playbooks/11-create-demo-ingress.yml --ask-vault-pass
ansible-playbook playbooks/12-install-cert-manager.yml --ask-vault-pass
ansible-playbook playbooks/13-create-demo-tls.yml --ask-vault-pass
ansible-playbook playbooks/14-install-gateway-api.yml --ask-vault-pass
ansible-playbook playbooks/15-deploy-data-platform.yml --ask-vault-pass
ansible-playbook playbooks/06-verify-cluster.yml --ask-vault-pass
```

### Data Platform Deployment

```bash
ansible-playbook playbooks/15-deploy-data-platform.yml --ask-vault-pass
```

Dieses Playbook deployt:

```text
Namespace data-platform
GHCR imagePullSecret
PostgreSQL Secret
Local PersistentVolume
PostgreSQL PVC
PostgreSQL Deployment + Service
Data API Deployment + Service
Data API HTTPRoute
Data Generator CronJob
Data Processing CronJob
Metabase DB Init Job
Metabase Deployment + Service
Metabase HTTPRoute
```

---

## Verify-Checks

Das Verify-Playbook prüft aktuell:

```text
containerd Status
kubelet Status
Helm Version
Kubernetes Nodes
System Pods
ingress-nginx Controller
ingress-nginx Service
Demo Ingress
cert-manager Pods
Certificate Status
TLS Secret
TLS Binding im Ingress
NGINX Gateway Fabric Pods
GatewayClass
Gateway
HTTPRoute
Gateway NodePort Service
Data Platform Pods
Data Platform Services
Data Platform PVCs
Data Generator CronJob
Data Platform Jobs
Data API Health über Gateway API
Metabase Health über Gateway API
PostgreSQL Tabellen
service_metrics Record Count
incidents Record Count
```

Erwarteter Zustand:

```text
k8s-master-01       Ready
k8s-worker-01       Ready
demo-nginx          Running
ingress-nginx       Running
cert-manager        Running
demo-local-tls      Ready=True
gatewayclass nginx  Accepted=True
demo-gateway        Programmed=True
data-api            Running
postgres            Running
metabase            Running
data-generator      CronJob vorhanden
postgres-data       Bound
api.data.local      erreichbar
dashboard.data.local erreichbar
```

Beispiel aus dem Verify-Output:

```text
Data API Gateway Health: {"status":"healthy","service":"data-api"}
HTTP/1.1 200 OK
service_metrics count: 310
incidents count: 64
```

---

## Idempotenz

Ein wichtiger Fokus dieses Labs ist Idempotenz.

Das bedeutet: Wenn der gewünschte Zustand bereits vorhanden ist, verändert Ansible nichts mehr.

```bash
ansible-playbook playbooks/site.yml --ask-vault-pass
ansible-playbook playbooks/14-install-gateway-api.yml --ask-vault-pass
ansible-playbook playbooks/15-deploy-data-platform.yml --ask-vault-pass
ansible-playbook playbooks/06-verify-cluster.yml --ask-vault-pass
```

Erwarteter Zustand bei erneutem Lauf:

```text
changed=0
failed=0
unreachable=0
```

---

## Zugriff auf die Demo-App

### HTTP über Ingress

```bash
curl -H "Host: demo.local" http://192.168.1.15:30520
curl -H "Host: demo.local" http://192.168.1.16:30520
```

### HTTPS über Ingress

```bash
curl -k https://demo.local:32685
curl -k --resolve demo.local:32685:192.168.1.15 https://demo.local:32685
```

### HTTP über Gateway API

```bash
curl -H "Host: gateway.demo.local" http://192.168.1.16:31977
```

---

## Zugriff auf die Data Platform

### Data API

```bash
curl -H "Host: api.data.local" http://192.168.1.16:31977/health
```

Erwartung:

```json
{"status":"healthy","service":"data-api"}
```

### Metabase Dashboard

```text
http://dashboard.data.local:31977
```

Metabase verbindet sich mit PostgreSQL:

```text
Host: postgres
Port: 5432
Database: dataplatform
Username: dataplatform
Password: dataplatform
```

Dashboard-Ideen:

```text
Metric Events by Service
Average Response Time by Service
Average Error Rate by Service
Incidents by Severity
Service Health Score
Service Health Summary
```

---

## Windows hosts-Datei

Für den Browser-Test unter Windows müssen die Hostnames lokal auf den Worker-Node zeigen.

Datei als Administrator öffnen:

```text
C:\Windows\System32\drivers\etc\hosts
```

Einträge:

```text
192.168.1.15 demo.local
192.168.1.16 gateway.demo.local
192.168.1.16 api.data.local
192.168.1.16 dashboard.data.local
```

Danach im Browser:

```text
http://demo.local:30520
https://demo.local:32685
http://gateway.demo.local:31977
http://api.data.local:31977/health
http://dashboard.data.local:31977
```

---

## Container Images

Eigene Images werden in GitHub Container Registry veröffentlicht:

```text
ghcr.io/elmed05/data-platform-api:0.1.0
ghcr.io/elmed05/data-generator:0.1.0
```

Kubernetes zieht diese Images über ein Image Pull Secret:

```text
Secret: ghcr-secret
Namespace: data-platform
```

Das Secret wird über Ansible aus Vault-Daten erzeugt.

---

## Storage

PostgreSQL nutzt ein lokales PersistentVolume auf dem Worker-Node.

```text
Node: k8s-worker-01
Pfad: /mnt/data-platform/postgres
PV: postgres-local-pv
PVC: postgres-data
StorageClass: local-storage
Access Mode: ReadWriteOnce
```

Der Storage ist bewusst einfach gehalten, aber persistent und nachvollziehbar.

Für produktionsähnlichere Setups wären später möglich:

```text
Longhorn
OpenEBS
NFS Provisioner
Ceph/Rook
Cloud Block Storage
```

---

## Wichtige Kubernetes-Konzepte in diesem Lab

```text
Deployment
ReplicaSet
Pod
Service
ClusterIP
NodePort
PersistentVolume
PersistentVolumeClaim
CronJob
Secret
Ingress
IngressClass
Gateway API
GatewayClass
Gateway
HTTPRoute
cert-manager
Certificate
TLS Secret
```

Aktuelle Gateway API Hostnames:

```text
gateway.demo.local     → demo-nginx
api.data.local         → data-api
dashboard.data.local   → metabase
```

---

## Typische Traffic Flows

### Demo-App über Ingress

```text
Client
→ demo.local:30520
→ ingress-nginx-controller
→ Ingress Rule
→ demo-nginx ClusterIP Service
→ demo-nginx Pod
```

### Demo-App über HTTPS Ingress

```text
Client
→ demo.local:32685
→ ingress-nginx-controller
→ TLS termination mit demo-local-tls
→ Ingress Rule
→ demo-nginx ClusterIP Service
→ demo-nginx Pod
```

### Demo-App über Gateway API

```text
Client
→ gateway.demo.local:31977
→ demo-gateway-nginx NodePort
→ Gateway demo-gateway
→ HTTPRoute demo-nginx-route
→ demo-nginx ClusterIP Service
→ demo-nginx Pod
```

### Data API über Gateway API

```text
Client
→ api.data.local:31977
→ demo-gateway-nginx NodePort
→ Gateway demo-gateway
→ HTTPRoute data-api-route
→ data-api ClusterIP Service
→ data-api Pod
→ PostgreSQL
```

### Metabase über Gateway API

```text
Client
→ dashboard.data.local:31977
→ demo-gateway-nginx NodePort
→ Gateway demo-gateway
→ HTTPRoute metabase-route
→ metabase ClusterIP Service
→ Metabase Pod
→ PostgreSQL
```

---

## Nützliche kubectl-Befehle

### Nodes prüfen

```bash
kubectl get nodes -o wide
```

### Alle Pods prüfen

```bash
kubectl get pods -A -o wide
```

### Demo-App prüfen

```bash
kubectl get all -n demo
```

### Ingress prüfen

```bash
kubectl get ingress -n demo
kubectl describe ingress demo-nginx -n demo
```

### Gateway API prüfen

```bash
kubectl get pods -n nginx-gateway -o wide
kubectl get svc -n nginx-gateway
kubectl get gatewayclass
kubectl get gateway -A
kubectl get httproute -A
kubectl describe gateway demo-gateway -n nginx-gateway
kubectl describe httproute demo-nginx-route -n demo
kubectl describe httproute data-api-route -n data-platform
kubectl describe httproute metabase-route -n data-platform
```

### Data Platform prüfen

```bash
kubectl get all -n data-platform
kubectl get pods -n data-platform -o wide
kubectl get svc -n data-platform
kubectl get pvc -n data-platform
kubectl get cronjob -n data-platform
kubectl get jobs -n data-platform
```

### PostgreSQL Tabellen prüfen

```bash
kubectl exec -n data-platform deploy/postgres -- \
  psql -U dataplatform -d dataplatform -c '\dt'
```

### Anzahl der Metriken prüfen

```bash
kubectl exec -n data-platform deploy/postgres -- \
  psql -U dataplatform -d dataplatform \
  -c 'SELECT service_name, COUNT(*) FROM service_metrics GROUP BY service_name ORDER BY service_name;'
```

### Incidents prüfen

```bash
kubectl exec -n data-platform deploy/postgres -- \
  psql -U dataplatform -d dataplatform \
  -c 'SELECT service_name, severity, COUNT(*) FROM incidents GROUP BY service_name, severity ORDER BY service_name;'
```

### Service Health Summary prüfen

```bash
kubectl exec -n data-platform deploy/postgres -- \
  psql -U dataplatform -d dataplatform \
  -c 'SELECT service_name, avg_error_rate, incident_count, health_score, calculated_at FROM service_health_summary ORDER BY health_score ASC;'
```

### Data Processing Job manuell starten

```bash
kubectl create job --from=cronjob/data-processing data-processing-manual -n data-platform
kubectl logs -n data-platform -l job-name=data-processing-manual --tail=100
```

### MinIO Processed Zone prüfen

```bash
kubectl run mc-check-processed -n data-platform --rm -i --restart=Never --image=minio/mc \
  --command -- /bin/sh -c "mc alias set local http://minio-api:9000 <USER> <PASSWORD> && mc find local/processed --maxdepth 10"
```

---

## Sicherheitsnotizen

- SSH-Zugriff läuft per SSH-Key.
- sudo-Passwörter werden mit Ansible Vault verwaltet.
- GHCR Token wird mit Ansible Vault verwaltet.
- kubeadm Join Tokens werden nicht dauerhaft benötigt.
- Das Join-Playbook erzeugt nur dann neue Tokens, wenn Worker noch nicht gejoint sind.
- Join Tokens werden nicht im Ansible Output angezeigt.
- Das aktuelle TLS-Zertifikat ist Self-Signed und nur für das lokale Lab gedacht.
- Für produktionsähnliche Umgebungen wären eine interne CA, ACME oder Let’s Encrypt sinnvoll.
- Der Gateway API NodePort nutzt aktuell `externalTrafficPolicy: Local`; dadurch ist der externe Zugriff an den Node mit lokalem Gateway-Pod gebunden.
- PostgreSQL-Zugangsdaten sind für das lokale Lab einfach gehalten.
- Für produktionsnähere Setups wären External Secrets, Sealed Secrets oder Vault sinnvoll.
- Für produktionsnähere Datenhaltung wären replizierter Storage und Backup/Restore wichtig.
- In produktionsnahen Umgebungen würde man vor Gateway/Ingress typischerweise LoadBalancer, MetalLB, Cloud Load Balancer oder eine dedizierte Edge-Komponente verwenden.

---

---

## Helm Chart

Die Data Platform wurde zusätzlich als Helm Chart vorbereitet.

Das Chart rendert die Kubernetes-Ressourcen für:

- data-api
- data-generator CronJob
- data-processing CronJob
- metabase
- minio
- Services
- HTTPRoutes

Secrets, Namespace sowie persistente Storage-Ressourcen bleiben aktuell bewusst unter Ansible-Kontrolle.

Prüfung:

```bash
helm lint apps/data-platform/chart
helm template data-platform apps/data-platform/chart > /tmp/data-platform-rendered.yaml
kubectl apply --dry-run=server -f /tmp/data-platform-rendered.yaml
```

---



## Aktueller Lernstand

Mit diesem Lab wurden bisher folgende Themen praktisch umgesetzt:

```text
Linux Server Setup
SSH-Key Zugriff
Ansible Automation
Ansible Vault
Ansible Rollenstruktur
Idempotente Playbooks
containerd
kubeadm
kubelet
kubectl
Kubernetes Control Plane
Worker Node Join
Flannel CNI
Helm
Deployment
ReplicaSet
Pod
Service
ClusterIP
NodePort
Ingress
IngressClass
ingress-nginx
cert-manager
Certificate
TLS Secret
HTTPS Ingress
Gateway API
GatewayClass
Gateway
HTTPRoute
NGINX Gateway Fabric
externalTrafficPolicy Local
PersistentVolume
PersistentVolumeClaim
PostgreSQL auf Kubernetes
Private Container Registry / GHCR
ImagePullSecret
FastAPI auf Kubernetes
Kubernetes CronJob
Metabase Dashboard
Data Ingestion
Data Platform Verification
Cluster Verification
```

---

## Projektziel

Das Ziel dieses Labs ist es, eine realistische Kubernetes-Lernumgebung aufzubauen, die typische DevOps-, Platform-Engineering- und Data-Platform-Themen abdeckt.

Der Fokus liegt nicht nur auf Installation, sondern auf einem nachvollziehbaren Betriebsmodell:

```text
Server automatisiert vorbereiten
Cluster reproduzierbar aufbauen
Worker Nodes verwalten
Workloads deployen
Ingress, TLS und Gateway API betreiben
Data Platform betreiben
Daten automatisch erzeugen
Daten über API aufnehmen
Daten persistent speichern
Daten über Dashboard sichtbar machen
Cluster- und Plattformzustand verifizieren
Änderungen versionieren
```

Dieses Projekt eignet sich als Grundlage für weitere Themen wie GitOps, Observability, CI/CD, Security, Lakehouse, Data Processing und MLOps.

---

## Nächste Lernschritte

### Kurzfristig

```text
README und Architekturdiagramme aktualisieren
Screenshots vom Metabase Dashboard dokumentieren
Verify-Playbook weiter strukturieren
Data Platform Rolle weiter aufräumen
Manifeste perspektivisch in Helm Chart überführen
```

### Data Platform / Lakehouse Foundation

```text
MinIO als S3-kompatibler Object Storage
Raw Zone für rohe Events
Processed Zone für transformierte Daten
Curated Zone für aggregierte Daten
Data Processing Job
Service Health Summary Tabelle
```

### MLOps Foundation

```text
MLflow Tracking Server
PostgreSQL als MLflow Backend Store
MinIO als MLflow Artifact Store
Training Job für Service Risk Prediction
Model Metrics und Experimente dokumentieren
```

### GitOps

```text
Argo CD installieren
Data Platform über GitOps verwalten
App-of-Apps Struktur
Automatischer Sync aus Git
```

### Observability

```text
Prometheus und Grafana
kube-state-metrics
CronJob Monitoring
Data API Metriken
PostgreSQL Monitoring
Gateway/Ingress Monitoring
Optional Loki Logging
Optional OpenTelemetry Collector
```

### Security und Betrieb

```text
RBAC
Network Policies
Secrets Management
Backup/Restore mit Velero
Storage mit Longhorn/OpenEBS
TLS für Gateway API
Image Scanning
CI/CD Pipeline für Container Images
```
