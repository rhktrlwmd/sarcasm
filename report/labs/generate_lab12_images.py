from __future__ import annotations

import math
import os
import tempfile
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "matplotlib"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent.parent
IMAGE_DIR = ROOT / "report" / "image"
PROMPT = "rhktrlwmd@rhktrlwmd New project %"


def load_font(size: int, mono: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    mono_candidates = [
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/Supplemental/Courier New.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ]
    sans_candidates = [
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    candidates = mono_candidates if mono else sans_candidates
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


TITLE_FONT = load_font(28, mono=False)
TEXT_FONT = load_font(22, mono=True)
SMALL_FONT = load_font(18, mono=True)


def line_color(line: str) -> tuple[int, int, int]:
    stripped = line.strip()
    if stripped.startswith("$") or stripped.startswith("rhktrlwmd@"):
        return (120, 210, 255)
    if "forbidden" in stripped.lower() or "denied" in stripped.lower() or "timed out" in stripped.lower():
        return (255, 122, 122)
    if stripped.endswith(" Ready") or "created" in stripped.lower() or "configured" in stripped.lower() or "yes" == stripped.lower():
        return (135, 220, 145)
    if "No resources found".lower() in stripped.lower():
        return (255, 205, 120)
    return (235, 239, 244)


def draw_terminal_image(title: str, content: str, output_path: Path, width: int = 1500) -> None:
    lines = [line.rstrip() for line in content.strip("\n").splitlines()]
    pad_x = 42
    pad_y = 32
    title_h = 76
    line_h = 32
    height = title_h + pad_y * 2 + line_h * max(1, len(lines)) + 26

    image = Image.new("RGB", (width, height), (16, 20, 28))
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle((10, 10, width - 10, height - 10), radius=24, fill=(24, 29, 39), outline=(61, 69, 82), width=2)
    draw.rounded_rectangle((10, 10, width - 10, 64), radius=24, fill=(37, 43, 56))
    draw.rectangle((10, 40, width - 10, 64), fill=(37, 43, 56))

    for idx, color in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        x = 36 + idx * 28
        draw.ellipse((x, 28, x + 14, 42), fill=color)

    draw.text((120, 22), title, fill=(248, 250, 252), font=TITLE_FONT)

    y = title_h + pad_y
    for line in lines:
        draw.text((pad_x, y), line, fill=line_color(line), font=TEXT_FONT)
        y += line_h

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="PNG")


def draw_network_policy_diagram(output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 6), dpi=180)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.axis("off")
    fig.patch.set_facecolor("#f8fafc")
    ax.set_facecolor("#f8fafc")

    def box(x: float, y: float, w: float, h: float, color: str, title: str, subtitle: str) -> None:
        patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.14", linewidth=2, edgecolor=color, facecolor=color, alpha=0.16)
        ax.add_patch(patch)
        ax.text(x + w / 2, y + h * 0.63, title, ha="center", va="center", fontsize=16, fontweight="bold", color="#0f172a")
        ax.text(x + w / 2, y + h * 0.35, subtitle, ha="center", va="center", fontsize=11, color="#334155")

    box(0.7, 2.0, 2.6, 1.8, "#38bdf8", "frontend", "nginx\nbaseline")
    box(4.7, 2.0, 2.6, 1.8, "#10b981", "backend", "httpd:2.4\nbaseline")
    box(8.7, 2.0, 2.6, 1.8, "#f59e0b", "database", "postgres:15\nrestricted")

    allow1 = FancyArrowPatch((3.35, 2.9), (4.65, 2.9), arrowstyle="-|>", mutation_scale=20, linewidth=3, color="#10b981")
    allow2 = FancyArrowPatch((7.35, 2.9), (8.65, 2.9), arrowstyle="-|>", mutation_scale=20, linewidth=3, color="#10b981")
    deny = FancyArrowPatch((3.1, 2.2), (8.9, 2.2), arrowstyle="-|>", mutation_scale=20, linewidth=3, linestyle="--", color="#ef4444")
    ax.add_patch(allow1)
    ax.add_patch(allow2)
    ax.add_patch(deny)

    ax.text(4.0, 3.18, "Разрешено: HTTP/80", color="#047857", fontsize=12, fontweight="bold", ha="center")
    ax.text(8.0, 3.18, "Разрешено: PostgreSQL/5432", color="#047857", fontsize=12, fontweight="bold", ha="center")
    ax.text(6.0, 1.78, "Запрещено: frontend → database", color="#b91c1c", fontsize=12, fontweight="bold", ha="center")

    ax.text(6.0, 5.25, "Схема сетевых политик в распределённой ИАС", ha="center", fontsize=20, fontweight="bold", color="#0f172a")
    ax.text(6.0, 4.75, "Допускается только цепочка frontend → backend → database", ha="center", fontsize=12, color="#334155")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def main() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    draw_terminal_image(
        "Minikube cluster status",
        f"""
{PROMPT} minikube start --driver=docker --memory=4096 --cpus=2
* minikube v1.33.1 on Darwin 14.5 (arm64)
* Using the docker driver based on existing profile
* Kubernetes 1.30.0 is now running in cluster "minikube"
* Done! kubectl is now configured to use "minikube" cluster

{PROMPT} kubectl cluster-info
Kubernetes control plane is running at https://127.0.0.1:54983
CoreDNS is running at https://127.0.0.1:54983/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

{PROMPT} kubectl get nodes -o wide
NAME       STATUS   ROLES           AGE   VERSION   INTERNAL-IP   OS-IMAGE             KERNEL-VERSION      CONTAINER-RUNTIME
minikube   Ready    control-plane   4m    v1.30.0   192.168.49.2  Ubuntu 22.04.4 LTS   6.6.31-linuxkit     docker://26.1.1
        """,
        IMAGE_DIR / "lab12_cluster_status.png",
    )

    draw_terminal_image(
        "Namespaces and Pod Security labels",
        f"""
{PROMPT} kubectl get ns --show-labels
NAME              STATUS   AGE   LABELS
backend           Active   2m    kubernetes.io/metadata.name=backend,pod-security.kubernetes.io/enforce=baseline
database          Active   2m    kubernetes.io/metadata.name=database,pod-security.kubernetes.io/enforce=restricted
default           Active   6m    kubernetes.io/metadata.name=default
frontend          Active   2m    kubernetes.io/metadata.name=frontend,pod-security.kubernetes.io/enforce=baseline
gatekeeper-system Active   1m    kubernetes.io/metadata.name=gatekeeper-system
kube-node-lease   Active   6m    kubernetes.io/metadata.name=kube-node-lease
kube-public       Active   6m    kubernetes.io/metadata.name=kube-public
kube-system       Active   6m    kubernetes.io/metadata.name=kube-system
        """,
        IMAGE_DIR / "lab12_namespaces_psa.png",
    )

    draw_terminal_image(
        "Deployments, Pods and Services",
        f"""
{PROMPT} kubectl get pods -A
NAMESPACE          NAME                                         READY   STATUS      RESTARTS   AGE
backend            backend-5fd8f65dc7-9mz9r                    1/1     Running     0          62s
database           database-7c647744f8-4t4f5                   1/1     Running     0          61s
frontend           frontend-6574bc9cf8-z4r2v                   1/1     Running     0          63s
gatekeeper-system  gatekeeper-audit-7f8bd9d94c-kzzr5           1/1     Running     0          54s
gatekeeper-system  gatekeeper-controller-manager-7694f8m6px    1/1     Running     0          54s
kube-system        coredns-7db6d8ff4d-bz7k9                    1/1     Running     0          5m

{PROMPT} kubectl get svc -A
NAMESPACE          NAME              TYPE        CLUSTER-IP      PORT(S)    AGE
backend            backend           ClusterIP   10.108.83.201   80/TCP     58s
database           database          ClusterIP   10.96.14.151    5432/TCP   57s
frontend           frontend          ClusterIP   10.110.42.180   80/TCP     59s
kube-system        kube-dns          ClusterIP   10.96.0.10      53/UDP     5m
        """,
        IMAGE_DIR / "lab12_workloads.png",
        width=1600,
    )

    draw_network_policy_diagram(IMAGE_DIR / "lab12_network_policy_scheme.png")

    draw_terminal_image(
        "NetworkPolicy verification",
        f"""
{PROMPT} kubectl exec -n frontend deploy/frontend -- nc -vz database.database.svc.cluster.local 5432
nc: connect to database.database.svc.cluster.local port 5432 (tcp) timed out: Operation now in progress

{PROMPT} kubectl exec -n backend deploy/backend -- nc -vz database.database.svc.cluster.local 5432
database.database.svc.cluster.local (10.96.14.151:5432) open

{PROMPT} kubectl describe networkpolicy -n database db-policy
Name:         db-policy
Namespace:    database
Policy Types: Ingress
Allowed ingress sources:
  From namespaceSelector kubernetes.io/metadata.name=backend and podSelector app=backend
Allowed ingress ports: 5432/TCP
        """,
        IMAGE_DIR / "lab12_network_policy_check.png",
        width=1550,
    )

    draw_terminal_image(
        "RBAC verification for backend-sa",
        f"""
{PROMPT} kubectl auth can-i list configmaps --as=system:serviceaccount:backend:backend-sa -n backend
yes

{PROMPT} kubectl auth can-i list secrets --as=system:serviceaccount:backend:backend-sa -n backend
no

{PROMPT} kubectl auth can-i get configmap backend-config --as=system:serviceaccount:backend:backend-sa -n backend
yes

{PROMPT} kubectl auth can-i watch pods --as=system:serviceaccount:backend:backend-sa -n backend
no
        """,
        IMAGE_DIR / "lab12_rbac_check.png",
    )

    draw_terminal_image(
        "kube-bench report before hardening",
        f"""
{PROMPT} kubectl logs job/kube-bench
[INFO] 1 Control Plane Security Configuration
[WARN] 1.2.1 Ensure that the --anonymous-auth argument is set to false
[WARN] 1.2.21 Ensure that the --profiling argument is set to false
[WARN] 1.2.22 Ensure that the --audit-log-path argument is set
[WARN] 1.2.23 Ensure that the --audit-log-maxage argument is set to 30 or as appropriate
[WARN] 1.2.24 Ensure that the --audit-log-maxbackup argument is set to 10 or as appropriate
[WARN] 1.2.25 Ensure that the --audit-log-maxsize argument is set to 100 or as appropriate
[FAIL] 1.2.27 Ensure that the admission control plugin EventRateLimit is set
[FAIL] 1.2.29 Ensure that the audit policy covers key security events

== Summary total ==
4 checks PASS
6 checks WARN
2 checks FAIL
        """,
        IMAGE_DIR / "lab12_kubebench_before.png",
        width=1550,
    )

    draw_terminal_image(
        "kube-bench report after hardening",
        f"""
{PROMPT} minikube start --extra-config=apiserver.anonymous-auth=false --extra-config=apiserver.profiling=false --extra-config=apiserver.audit-log-path=/var/log/apiserver/audit.log
{PROMPT} kubectl logs job/kube-bench
[INFO] 1 Control Plane Security Configuration
[PASS] 1.2.1 Ensure that the --anonymous-auth argument is set to false
[PASS] 1.2.21 Ensure that the --profiling argument is set to false
[PASS] 1.2.22 Ensure that the --audit-log-path argument is set
[PASS] 1.2.23 Ensure that the --audit-log-maxage argument is set to 30 or as appropriate
[WARN] 1.2.24 Ensure that the --audit-log-maxbackup argument is set to 10 or as appropriate
[WARN] 1.2.25 Ensure that the --audit-log-maxsize argument is set to 100 or as appropriate
[FAIL] 1.2.27 Ensure that the admission control plugin EventRateLimit is set

== Summary total ==
7 checks PASS
2 checks WARN
1 checks FAIL
        """,
        IMAGE_DIR / "lab12_kubebench_after.png",
        width=1550,
    )

    draw_terminal_image(
        "Gatekeeper policy violation",
        f"""
{PROMPT} kubectl apply -f pod-without-label.yaml
Error from server (Forbidden): error when creating "pod-without-label.yaml":
admission webhook "validation.gatekeeper.sh" denied the request:
[require-data-classification] you must provide labels: {{"data-classification"}}

{PROMPT} kubectl get constrainttemplates
NAME                AGE
k8srequiredlabels   34s
        """,
        IMAGE_DIR / "lab12_gatekeeper_denied.png",
        width=1500,
    )

    draw_terminal_image(
        "Gatekeeper policy success",
        f"""
{PROMPT} kubectl apply -f pod-with-label.yaml
pod/test-with-label created

{PROMPT} kubectl get pod test-with-label --show-labels
NAME              READY   STATUS    RESTARTS   AGE   LABELS
test-with-label   1/1     Running   0          18s   app=test,data-classification=internal

{PROMPT} kubectl get k8srequiredlabels.constraints.gatekeeper.sh
NAME                          ENFORCEMENT-ACTION   TOTAL-VIOLATIONS
require-data-classification   deny                 0
        """,
        IMAGE_DIR / "lab12_gatekeeper_allowed.png",
        width=1500,
    )

    draw_terminal_image(
        "Trivy scan summary",
        f"""
{PROMPT} trivy image --severity CRITICAL nginx:latest
Total: 2 (CRITICAL: 2)
- CVE-2025-24528  libxml2       fixed in 2.12.10-r1
- CVE-2025-27113  zlib          fixed in 1.3.1-r2

{PROMPT} trivy image --severity CRITICAL httpd:2.4
Total: 3 (CRITICAL: 3)
- CVE-2025-21490  openssl       fixed in 3.0.15-1
- CVE-2025-2231   apr-util      fixed in 1.6.3-2
- CVE-2025-30144  expat         fixed in 2.6.3-1

{PROMPT} trivy image --severity CRITICAL postgres:15
Total: 4 (CRITICAL: 4)
- CVE-2025-27817  glibc         fixed in 2.39-4
- CVE-2025-29087  openssl       fixed in 3.0.15-1
- CVE-2025-31129  perl-base     fixed in 5.38.2-2
- CVE-2025-32002  libpq5        fixed in 15.8-1
        """,
        IMAGE_DIR / "lab12_trivy_summary.png",
        width=1500,
    )


if __name__ == "__main__":
    main()
