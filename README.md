# Linux Kubernetes Lab mit Ansible, Helm, Ingress, TLS und Gateway API

Dieses Projekt baut ein praxisnahes Kubernetes-Lab auf Basis von Ubuntu Server VMs in VMware Workstation auf.

Ziel ist es, Kubernetes, Linux-Server-Administration, Ansible-Automatisierung und typische Plattform-Komponenten realistisch zu lernen — nicht nur mit Minikube, sondern mit echten Linux-Servern, kubeadm, containerd, Helm, Ingress, TLS und Gateway API.

Das Lab besteht aktuell aus einem Multi-Node Kubernetes Cluster mit einem Control-Plane-Node und einem Worker-Node.

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
    └── Flannel CNI
```

---

## App-Zugriffsarchitektur

Die Demo-Anwendung läuft intern im Cluster als `ClusterIP` Service. Sie wird über zwei unterschiedliche Kubernetes-Networking-Modelle veröffentlicht:

```text
1. Klassisch über ingress-nginx und Ingress
2. Modern über Gateway API mit NGINX Gateway Fabric
```

### Zugriff über Ingress

```text
Browser / curl
→ demo.local:32685
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
http://gateway.demo.local:31977
```

Da aktuell ein Self-Signed-Zertifikat genutzt wird, zeigt der Browser bei HTTPS eine Zertifikatswarnung.

### Zugriff über Gateway API

Zusätzlich ist die Demo-Anwendung über Gateway API erreichbar.

```text
Browser / curl
→ gateway.demo.local:31977
→ demo-gateway-nginx NodePort
→ Gateway demo-gateway
→ HTTPRoute demo-nginx-route
→ demo-nginx ClusterIP Service
→ demo-nginx Pod
```

Aktueller Gateway-API-Zugriff:

```text
HTTP:
http://gateway.demo.local:31977
```

Wichtig: Der Gateway-Service nutzt aktuell `externalTrafficPolicy: Local`. Deshalb funktioniert der NodePort-Zugriff über den Worker-Node, auf dem der Gateway-Pod läuft:

```text
k8s-worker-01 / 192.168.0.173
```

Test:

```bash
curl -H "Host: gateway.demo.local" http://192.168.0.173:31977
```

---

## Aktueller Stand

- Ubuntu Server VMs in VMware Workstation
- Multi-Node Kubernetes Cluster
- Control Plane Node: `k8s-master-01`
- Worker Node: `k8s-worker-01`
- SSH-Key-basierter Zugriff
- Ansible Inventory und Playbooks
- Ansible Vault für sudo-Zugangsdaten
- Zentrales `site.yml` Playbook für den kompletten Lab-Aufbau
- Ansible-Rollenstruktur für wiederverwendbare Automatisierung
- Idempotente Playbooks: erneuter Lauf endet mit `changed=0`
- Kubernetes-Manifeste versioniert im Repository unter `manifests/`
- containerd als Container Runtime
- Kubernetes v1.36 mit kubeadm
- Flannel als CNI
- Helm installiert
- Demo-App `nginx` per Helm deployed
- Demo-App Service als `ClusterIP`
- ingress-nginx als Ingress Controller
- Routing über `demo.local`
- cert-manager installiert
- Self-Signed TLS-Zertifikat für `demo.local`
- HTTPS Zugriff über Ingress
- Gateway API CRDs installiert
- NGINX Gateway Fabric als Gateway API Controller installiert
- GatewayClass `nginx` vorhanden und accepted
- Gateway `demo-gateway` programmiert und aktiv
- HTTPRoute `demo-nginx-route` für `gateway.demo.local`
- Demo-App zusätzlich über Gateway API erreichbar
- Verify-Playbook zur Cluster-Prüfung
- Worker-Join-Playbook ist idempotent
- kubeadm Join Tokens werden nur erzeugt, wenn Worker noch nicht gejoint sind
- Keine offenen kubeadm Join Tokens nach erfolgreichem Join nötig
- `site.yml` läuft idempotent mit `changed=0`

---

## Serverübersicht

| Hostname | Rolle | IP | Betriebssystem | Runtime |
|---|---|---|---|---|
| `k8s-master-01` | Control Plane | `192.168.0.202` | Ubuntu Server 24.04 LTS | containerd |
| `k8s-worker-01` | Worker Node | `192.168.0.173` | Ubuntu Server 24.04 LTS | containerd |

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
│       │   └── all.yml
│       └── host_vars/
│           ├── k8s-master-01/
│           │   └── vault.yml
│           └── k8s-worker-01/
│               └── vault.yml
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
│   └── 14-install-gateway-api.yml
├── roles/
│   ├── base_linux/
│   ├── cert_manager/
│   ├── containerd/
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
└── demo_tls/
    └── SelfSigned ClusterIssuer, Certificate und TLS Binding
```

Die Playbooks bleiben als klare Einstiegspunkte erhalten, rufen aber größtenteils nur noch die jeweiligen Rollen auf.

Beispiel:

```yaml
---
- name: Configure base Linux settings
  hosts: all
  become: true
  gather_facts: true

  roles:
    - base_linux
```

Dadurch bleibt die Automatisierung wartbarer, wiederverwendbarer und näher an einer professionellen Ansible-Struktur.

---

## Ansible Inventory

Beispiel:

```ini
[k8s_control_plane]
k8s-master-01 ansible_host=192.168.0.202 ansible_user=devops ansible_python_interpreter=/usr/bin/python3

[k8s_workers]
k8s-worker-01 ansible_host=192.168.0.173 ansible_user=devops ansible_python_interpreter=/usr/bin/python3

[k8s_cluster:children]
k8s_control_plane
k8s_workers
```

---

## Ansible Vault

Sudo-Passwörter werden nicht im Klartext im Repository gespeichert, sondern über Ansible Vault verschlüsselt.

Beispielstruktur:

```text
inventories/lab/host_vars/k8s-master-01/vault.yml
inventories/lab/host_vars/k8s-worker-01/vault.yml
```

Beispielinhalt vor Verschlüsselung:

```yaml
---
ansible_become_password: "SUDO_PASSWORD"
```

Ausführen mit Vault:

```bash
ansible-playbook playbooks/06-verify-cluster.yml --ask-vault-pass
```

---

## Playbook-Reihenfolge

Der komplette Lab-Aufbau kann über ein zentrales Playbook ausgeführt werden:

```bash
ansible-playbook playbooks/site.yml --ask-vault-pass
```

Dieses Playbook ruft die einzelnen Schritte in der richtigen Reihenfolge auf.

Ein erneuter Lauf sollte im Zielzustand ohne Änderungen enden:

```text
changed=0
failed=0
unreachable=0
```

Alternativ können die einzelnen Playbooks weiterhin separat ausgeführt werden.

### 1. Verbindung testen

```bash
ansible-playbook playbooks/00-ping.yml
```

### 2. Server für Ansible vorbereiten

```bash
ansible-playbook playbooks/01-bootstrap.yml --ask-vault-pass
```

### 3. Linux-Basiskonfiguration

```bash
ansible-playbook playbooks/02-base-linux.yml --ask-vault-pass
```

Dieses Playbook ruft die Rolle `base_linux` auf und setzt unter anderem:

```text
Basis-Pakete
Timezone
Hostname
/etc/hosts
Swap deaktivieren
```

### 4. Container Runtime installieren

```bash
ansible-playbook playbooks/03-container-runtime.yml --ask-vault-pass
```

Dieses Playbook ruft die Rolle `containerd` auf und installiert bzw. konfiguriert:

```text
containerd
overlay Kernel-Modul
br_netfilter Kernel-Modul
sysctl Settings für Kubernetes Networking
SystemdCgroup für containerd
```

### 5. Kubernetes-Pakete installieren

```bash
ansible-playbook playbooks/04-kubernetes-packages.yml --ask-vault-pass
```

Dieses Playbook ruft die Rolle `kubernetes_common` auf und installiert:

```text
kubeadm
kubelet
kubectl
```

### 6. Control Plane initialisieren

```bash
ansible-playbook playbooks/05-init-control-plane.yml --ask-vault-pass
```

Dieses Playbook ruft die Rolle `kubernetes_control_plane` auf, führt `kubeadm init` aus, richtet die kubeconfig ein und installiert Flannel als CNI.

### 7. Helm installieren

```bash
ansible-playbook playbooks/07-install-helm.yml --ask-vault-pass
```

Dieses Playbook ruft die Rolle `helm` auf.

### 8. Worker Nodes joinen

```bash
ansible-playbook playbooks/09-join-workers.yml --ask-vault-pass
```

Das Join-Playbook nutzt die Rolle `kubernetes_worker` und ist idempotent:

- Es prüft zuerst, ob Worker bereits gejoint sind.
- Es erzeugt nur dann einen kubeadm Join Token, wenn ein Worker noch nicht Teil des Clusters ist.
- Der Join Token wird nicht im Terminal ausgegeben.
- Bereits gejointe Worker werden übersprungen.

### 9. Demo-App deployen

```bash
ansible-playbook playbooks/08-deploy-test-app.yml --ask-vault-pass
```

Dieses Playbook ruft die Rolle `demo_app` auf.

Die Demo-App wird per Helm installiert:

```text
Namespace: demo
Release: demo-nginx
Service Type: ClusterIP
```

Die App ist bewusst nicht direkt per NodePort veröffentlicht, sondern wird über Ingress erreichbar gemacht.

### 10. ingress-nginx installieren

```bash
ansible-playbook playbooks/10-install-ingress-nginx.yml --ask-vault-pass
```

Dieses Playbook ruft die Rolle `ingress_nginx` auf.

Installiert den Ingress Controller per Helm:

```text
Namespace: ingress-nginx
IngressClass: nginx
Service Type: NodePort
HTTP NodePort: 30520
HTTPS NodePort: 32685
```

### 11. Demo-Ingress erstellen

```bash
ansible-playbook playbooks/11-create-demo-ingress.yml --ask-vault-pass
```

Dieses Playbook ruft die Rolle `demo_ingress` auf.

Erstellt eine Ingress Resource für:

```text
Host: demo.local
Service: demo-nginx
Port: 80
TLS Secret: demo-local-tls
```

### 12. cert-manager installieren

```bash
ansible-playbook playbooks/12-install-cert-manager.yml --ask-vault-pass
```

Dieses Playbook ruft die Rolle `cert_manager` auf.

Installiert:

```text
cert-manager
cert-manager-cainjector
cert-manager-webhook
cert-manager CRDs
```

### 13. TLS für Demo-Ingress erstellen

```bash
ansible-playbook playbooks/13-create-demo-tls.yml --ask-vault-pass
```

Dieses Playbook ruft die Rolle `demo_tls` auf.

Erstellt:

```text
SelfSigned ClusterIssuer
Certificate für demo.local
TLS Secret demo-local-tls
Ingress TLS Binding
```

### 14. Gateway API installieren und konfigurieren

```bash
ansible-playbook playbooks/14-install-gateway-api.yml --ask-vault-pass
```

Dieses Playbook ruft die Rolle `gateway_api` auf.

Erstellt und prüft:

```text
Gateway API CRDs
NGINX Gateway Fabric
GatewayClass nginx
Gateway demo-gateway
HTTPRoute demo-nginx-route
Gateway NodePort Service
```

### 15. Cluster prüfen

```bash
ansible-playbook playbooks/06-verify-cluster.yml --ask-vault-pass
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
```

Erwarteter Zustand:

```text
k8s-master-01   Ready
k8s-worker-01   Ready
demo-nginx      Running
ingress-nginx   Running
cert-manager    Running
demo-local-tls  Ready=True
gatewayclass   nginx Accepted=True
demo-gateway   Programmed=True
demo-nginx-route vorhanden
```

---

## Idempotenz

Ein wichtiger Fokus dieses Labs ist Idempotenz.

Das bedeutet: Wenn der gewünschte Zustand bereits vorhanden ist, verändert Ansible nichts mehr.

Der zentrale Test dafür ist:

```bash
ansible-playbook playbooks/site.yml --ask-vault-pass
```

Erwarteter Zustand bei erneutem Lauf:

```text
k8s-master-01   changed=0   failed=0   unreachable=0
k8s-worker-01   changed=0   failed=0   unreachable=0
```

Damit ist das Lab nicht nur manuell aufgebaut, sondern reproduzierbar und kontrolliert automatisiert.

---

## Zugriff auf die Demo-App

### HTTP über Ingress

```bash
curl -H "Host: demo.local" http://192.168.0.202:30520
```

Alternativ über den Worker:

```bash
curl -H "Host: demo.local" http://192.168.0.173:30520
```

### HTTPS über Ingress

Wenn `demo.local` in der lokalen hosts-Datei gesetzt ist:

```bash
curl -k https://demo.local:32685
http://gateway.demo.local:31977
```

Alternativ ohne hosts-Datei:

```bash
curl -k --resolve demo.local:32685:192.168.0.202 https://demo.local:32685
http://gateway.demo.local:31977
```

---

## Zugriff über Gateway API

Gateway API läuft parallel zum bestehenden Ingress-Setup.

Aktueller Zugriff:

```bash
curl -H "Host: gateway.demo.local" http://192.168.0.173:31977
```

Erwartung:

```text
HTTP/1.1 200 OK
Welcome to nginx!
```

Der Gateway-Service nutzt aktuell:

```text
externalTrafficPolicy: Local
```

Deshalb funktioniert der externe NodePort-Zugriff aktuell über den Worker-Node `192.168.0.173`, weil dort der Gateway-Pod läuft.

Wichtige Ressourcen:

```text
Namespace: nginx-gateway
GatewayClass: nginx
Gateway: demo-gateway
HTTPRoute: demo-nginx-route
Hostname: gateway.demo.local
NodePort: 31977
```

---

## Windows hosts-Datei

Für den Browser-Test unter Windows müssen `demo.local` und optional `gateway.demo.local` lokal auf Kubernetes Nodes zeigen.

Datei als Administrator öffnen:

```text
C:\Windows\System32\drivers\etc\hosts
```

Eintrag:

```text
192.168.0.202 demo.local
192.168.0.173 gateway.demo.local
```

Danach im Browser:

```text
http://demo.local:30520
https://demo.local:32685
http://gateway.demo.local:31977
```

Bei HTTPS erscheint wegen des Self-Signed-Zertifikats eine Zertifikatswarnung.

---

## Wichtige Kubernetes-Konzepte in diesem Lab

### Deployment

Das Deployment verwaltet die gewünschte Anzahl an Pods.

Beispiel:

```text
demo-nginx Deployment
→ erzeugt ReplicaSet
→ erzeugt Pod
```

### ReplicaSet

Das ReplicaSet sorgt dafür, dass die gewünschte Anzahl an Pods läuft.

### Pod

Der Pod ist die kleinste ausführbare Einheit in Kubernetes.

In diesem Lab läuft darin ein nginx Container.

### Service

Ein Service stellt eine stabile Adresse für Pods bereit.

Die Demo-App nutzt:

```text
ClusterIP
```

Dadurch ist sie nur intern im Cluster erreichbar.

### NodePort

NodePort wird aktuell nur für den Ingress Controller genutzt.

Dadurch kann Traffic von außen in den Cluster gelangen.

### Ingress

Ingress definiert HTTP/HTTPS-Routing-Regeln.

Beispiel:

```text
demo.local
→ demo-nginx Service
```

### Ingress Controller

Der ingress-nginx Controller setzt die Ingress-Regeln technisch um.

Ohne Ingress Controller hätte eine Ingress Resource keine Wirkung.

### IngressClass

Die IngressClass verbindet eine Ingress Resource mit einem konkreten Controller.

In diesem Lab:

```text
ingressClassName: nginx
```

### Gateway API

Gateway API ist ein moderneres Kubernetes-Networking-Modell als Ingress.

In diesem Lab wird Gateway API zusätzlich zum bestehenden Ingress-Setup betrieben.

### NGINX Gateway Fabric

NGINX Gateway Fabric ist der Gateway API Controller in diesem Lab.

Er setzt die Gateway API Ressourcen technisch um und erstellt den Gateway-Dataplane-Pod.

### GatewayClass

Die GatewayClass beschreibt, welcher Controller Gateway-Ressourcen verarbeitet.

In diesem Lab:

```text
GatewayClass: nginx
Controller: gateway.nginx.org/nginx-gateway-controller
Accepted: True
```

### Gateway

Das Gateway beschreibt den Einstiegspunkt für Traffic.

In diesem Lab:

```text
Gateway: demo-gateway
Namespace: nginx-gateway
Hostname: gateway.demo.local
Port: 80
Programmed: True
```

### HTTPRoute

Die HTTPRoute beschreibt die Routing-Regel von einem Hostnamen zu einem Backend-Service.

In diesem Lab:

```text
HTTPRoute: demo-nginx-route
Hostname: gateway.demo.local
Backend: demo-nginx
Port: 80
```

### cert-manager

cert-manager erstellt und verwaltet Kubernetes-Zertifikate automatisch.

In diesem Lab erstellt cert-manager ein Self-Signed-Zertifikat für `demo.local`.

### Certificate

Das Certificate beschreibt das gewünschte Zertifikat.

```text
Certificate: demo-local-tls
DNS Name: demo.local
Secret: demo-local-tls
```

### TLS Secret

Das TLS Secret enthält Zertifikat und Private Key.

```text
Secret: demo-local-tls
Type: kubernetes.io/tls
```

Der Ingress nutzt dieses Secret für HTTPS.

---

## Typischer Traffic Flow

### HTTP

```text
Client
→ demo.local:30520
→ ingress-nginx-controller
→ Ingress Rule
→ demo-nginx ClusterIP Service
→ demo-nginx Pod
```

### HTTPS

```text
Client
→ demo.local:32685
→ ingress-nginx-controller
→ TLS termination mit demo-local-tls
→ Ingress Rule
→ demo-nginx ClusterIP Service
→ demo-nginx Pod
```

Intern im Cluster geht der Traffic aktuell per HTTP weiter.

### Gateway API

```text
Client
→ gateway.demo.local:31977
→ demo-gateway-nginx NodePort
→ Gateway demo-gateway
→ HTTPRoute demo-nginx-route
→ demo-nginx ClusterIP Service
→ demo-nginx Pod
```

Auch hier bleibt der Backend-Service `demo-nginx` ein interner `ClusterIP` Service.

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

### Ingress Controller prüfen

```bash
kubectl get pods -n ingress-nginx -o wide
kubectl get svc -n ingress-nginx
kubectl get ingressclass
```

### cert-manager prüfen

```bash
kubectl get pods -n cert-manager -o wide
kubectl get certificate -n demo
kubectl describe certificate demo-local-tls -n demo
kubectl get secret demo-local-tls -n demo
```

### Gateway API prüfen

```bash
kubectl get pods -n nginx-gateway -o wide
kubectl get svc -n nginx-gateway
kubectl get gatewayclass
kubectl get gateway -A
kubectl get httproute -n demo
kubectl describe gateway demo-gateway -n nginx-gateway
kubectl describe httproute demo-nginx-route -n demo
```

### kubeadm Tokens prüfen

```bash
sudo kubeadm token list
```

---

## Sicherheitsnotizen

- SSH-Zugriff läuft per SSH-Key.
- sudo-Passwörter werden mit Ansible Vault verwaltet.
- kubeadm Join Tokens werden nicht dauerhaft benötigt.
- Das Join-Playbook erzeugt nur dann neue Tokens, wenn Worker noch nicht gejoint sind.
- Join Tokens werden nicht im Ansible Output angezeigt.
- Das aktuelle TLS-Zertifikat ist Self-Signed und nur für das lokale Lab gedacht.
- Für produktionsähnliche Umgebungen wären eine interne CA, ACME oder Let’s Encrypt sinnvoll.
- Der Gateway API NodePort nutzt aktuell `externalTrafficPolicy: Local`; dadurch ist der externe Zugriff an den Node mit lokalem Gateway-Pod gebunden.
- In produktionsnahen Umgebungen würde man vor Gateway/Ingress typischerweise LoadBalancer, MetalLB, Cloud Load Balancer oder eine dedizierte Edge-Komponente verwenden.

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
Cluster Verification
```

---

## Nächste Lernschritte

### Kurzfristig

```text
README und Architektur weiter pflegen
Rollenstruktur weiter verfeinern
Helm Values aus Playbooks in values-Dateien auslagern
Manifeste perspektivisch für GitOps vorbereiten
Verify-Playbook weiter verbessern
```

### Kubernetes Networking

```text
Ingress besser verstehen
TLS sauberer mit lokaler CA umsetzen
cert-manager Issuer/ClusterIssuer vertiefen
Network Policies lernen
```

### Moderne Kubernetes APIs

```text
Gateway API weiter vertiefen
HTTPRoute Features testen
Gateway API mit TLS erweitern
Vergleich Ingress vs Gateway API dokumentieren
```

### Plattform-Erweiterungen

```text
Prometheus und Grafana
Loki Logging
OpenTelemetry Collector
Argo CD GitOps
Container Registry Integration
CI/CD Pipeline für App-Deployments
RBAC
Secrets Management
Backup/Restore mit Velero
```

---

## Projektziel

Das Ziel dieses Labs ist es, eine realistische Kubernetes-Lernumgebung aufzubauen, die typische DevOps- und Platform-Engineering-Themen abdeckt.

Der Fokus liegt nicht nur auf Installation, sondern auf einem nachvollziehbaren Betriebsmodell:

```text
Server automatisiert vorbereiten
Cluster reproduzierbar aufbauen
Worker Nodes verwalten
Workloads deployen
Ingress, TLS und Gateway API betreiben
Cluster-Zustand verifizieren
Änderungen versionieren
```

Dieses Projekt eignet sich als Grundlage für weitere Themen wie GitOps, Observability, CI/CD, Security und Gateway API.
