from __future__ import annotations

import tempfile
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
REPORT_DIR = ROOT / "report"
IMAGE_DIR = REPORT_DIR / "image"
OUTPUT_DOCX = REPORT_DIR / "Отчет_ЛР12.docx"

TITLE = "Безопасность и комплаенс в распределённых информационно-аналитических системах"
LAB_NAME = "Лабораторная работа 12"
DISCIPLINE = "Разработка информационно-аналитических систем"
CITY_YEAR = "Москва, 2026"

CLUSTER_IMAGE = IMAGE_DIR / "lab12_cluster_status.png"
NAMESPACES_IMAGE = IMAGE_DIR / "lab12_namespaces_psa.png"
WORKLOADS_IMAGE = IMAGE_DIR / "lab12_workloads.png"
NETWORK_SCHEME_IMAGE = IMAGE_DIR / "lab12_network_policy_scheme.png"
NETWORK_CHECK_IMAGE = IMAGE_DIR / "lab12_network_policy_check.png"
RBAC_IMAGE = IMAGE_DIR / "lab12_rbac_check.png"
KUBEBENCH_BEFORE_IMAGE = IMAGE_DIR / "lab12_kubebench_before.png"
KUBEBENCH_AFTER_IMAGE = IMAGE_DIR / "lab12_kubebench_after.png"
GATEKEEPER_DENIED_IMAGE = IMAGE_DIR / "lab12_gatekeeper_denied.png"
GATEKEEPER_ALLOWED_IMAGE = IMAGE_DIR / "lab12_gatekeeper_allowed.png"
TRIVY_IMAGE = IMAGE_DIR / "lab12_trivy_summary.png"


def set_run_font(run, size: int = 14, bold: bool = False, italic: bool = False, font_name: str = "Times New Roman") -> None:
    run.font.name = font_name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), font_name)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic


def style_paragraph(paragraph, align=WD_ALIGN_PARAGRAPH.JUSTIFY, first_line_cm: float = 1.25) -> None:
    paragraph.alignment = align
    fmt = paragraph.paragraph_format
    fmt.first_line_indent = Cm(first_line_cm) if first_line_cm else None
    fmt.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    fmt.space_after = Pt(0)
    fmt.space_before = Pt(0)


def add_paragraph(document: Document, text: str = "", *, align=WD_ALIGN_PARAGRAPH.JUSTIFY, bold: bool = False, italic: bool = False, size: int = 14, first_line_cm: float = 1.25) -> None:
    paragraph = document.add_paragraph()
    style_paragraph(paragraph, align=align, first_line_cm=first_line_cm)
    run = paragraph.add_run(text)
    set_run_font(run, size=size, bold=bold, italic=italic)


def add_heading(document: Document, text: str, level: int = 1) -> None:
    size = 16 if level == 1 else 14
    paragraph = document.add_paragraph()
    style_paragraph(paragraph, align=WD_ALIGN_PARAGRAPH.LEFT, first_line_cm=0)
    run = paragraph.add_run(text)
    set_run_font(run, size=size, bold=True)


def add_bullet_list(document: Document, items: list[str]) -> None:
    for item in items:
        add_paragraph(document, f"• {item}", first_line_cm=0.8)


def add_code_block(document: Document, text: str) -> None:
    paragraph = document.add_paragraph()
    style_paragraph(paragraph, align=WD_ALIGN_PARAGRAPH.LEFT, first_line_cm=0)
    fmt = paragraph.paragraph_format
    fmt.left_indent = Cm(0.75)
    fmt.right_indent = Cm(0.4)
    for line in text.strip("\n").splitlines():
        run = paragraph.add_run(line + "\n")
        set_run_font(run, size=11, font_name="Courier New")


def add_table(document: Document, headers: list[str], rows: list[list[str]]) -> None:
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    for idx, header in enumerate(headers):
        cell_par = table.rows[0].cells[idx].paragraphs[0]
        style_paragraph(cell_par, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_cm=0)
        run = cell_par.add_run(header)
        set_run_font(run, size=12, bold=True)

    for row in rows:
        cells = table.add_row().cells
        for idx, value in enumerate(row):
            cell_par = cells[idx].paragraphs[0]
            style_paragraph(cell_par, align=WD_ALIGN_PARAGRAPH.LEFT, first_line_cm=0)
            run = cell_par.add_run(value)
            set_run_font(run, size=12)


def normalize_image_for_docx(image_path: Path) -> Path:
    with Image.open(image_path) as image:
        rgb = image.convert("RGB")
        temp_path = Path(tempfile.gettempdir()) / f"lab12_{image_path.stem}.png"
        rgb.save(temp_path, format="PNG")
    return temp_path


def add_image(document: Document, image_path: Path, caption: str, width_cm: float = 16.2) -> None:
    normalized = normalize_image_for_docx(image_path)
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.add_run().add_picture(str(normalized), width=Cm(width_cm))

    caption_paragraph = document.add_paragraph()
    style_paragraph(caption_paragraph, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_cm=0)
    run = caption_paragraph.add_run(caption)
    set_run_font(run, size=12, italic=True)


def add_page_break(document: Document) -> None:
    document.add_section(WD_SECTION.NEW_PAGE)


def build_title_page(document: Document) -> None:
    for _ in range(4):
        add_paragraph(document, "", first_line_cm=0)

    add_paragraph(document, "ОТЧЁТ", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=16, first_line_cm=0)
    add_paragraph(document, f"по {LAB_NAME.lower()}", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, first_line_cm=0)
    add_paragraph(document, f"по дисциплине «{DISCIPLINE}»", align=WD_ALIGN_PARAGRAPH.CENTER, first_line_cm=0)
    add_paragraph(document, "", first_line_cm=0)
    add_paragraph(document, f"Тема: «{TITLE}»", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, first_line_cm=0)

    for _ in range(10):
        add_paragraph(document, "", first_line_cm=0)

    add_paragraph(document, "Студент: ________________________________", align=WD_ALIGN_PARAGRAPH.RIGHT, first_line_cm=0)
    add_paragraph(document, "Группа: ________________________________", align=WD_ALIGN_PARAGRAPH.RIGHT, first_line_cm=0)
    add_paragraph(document, "Преподаватель: _________________________", align=WD_ALIGN_PARAGRAPH.RIGHT, first_line_cm=0)

    for _ in range(7):
        add_paragraph(document, "", first_line_cm=0)

    add_paragraph(document, CITY_YEAR, align=WD_ALIGN_PARAGRAPH.CENTER, first_line_cm=0)
    add_page_break(document)


def configure_document(document: Document) -> None:
    section = document.sections[0]
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)
    section.left_margin = Cm(3)
    section.right_margin = Cm(1.5)


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    document = Document()
    configure_document(document)
    build_title_page(document)

    add_heading(document, "1. Цель работы")
    add_paragraph(
        document,
        "Освоить практические методы обеспечения безопасности и контроля соответствия "
        "(комплаенс) в распределённых информационно-аналитических системах на примере "
        "контейнеризированной микросервисной платформы Kubernetes. В ходе работы изучаются "
        "сетевое разграничение, ролевое управление доступом, встроенные профили безопасности, "
        "проверка соответствия CIS Benchmark, policy-as-code и анализ уязвимостей контейнерных образов."
    )

    add_heading(document, "2. Краткие теоретические сведения")
    add_paragraph(
        document,
        "Распределённая информационно-аналитическая система включает сервисы сбора данных, "
        "обработки, хранения и предоставления результатов пользователю. При таком подходе растёт "
        "поверхность атаки: появляются межсервисные взаимодействия, сетевые маршруты, служебные "
        "учётные записи, образы контейнеров и настройки оркестратора. Поэтому безопасность должна "
        "строиться по принципам Zero Trust, минимальных привилегий и эшелонированной защиты."
    )
    add_bullet_list(
        document,
        [
            "NetworkPolicy ограничивает сетевое взаимодействие между подами и сервисами.",
            "Pod Security Standards задают допустимый уровень привилегий для запуска подов.",
            "RBAC разграничивает действия пользователей и сервисных учётных записей.",
            "CIS Kubernetes Benchmark помогает выявить небезопасные настройки кластера.",
            "OPA Gatekeeper реализует policy-as-code и проверяет ресурсы при создании.",
            "Trivy позволяет обнаружить уязвимости в образах и конфигурациях.",
        ],
    )
    add_paragraph(
        document,
        "Комплаенс в данном контексте означает не только защиту от атак, но и подтверждение того, "
        "что конфигурация среды соответствует принятым стандартам и организационным политикам."
    )

    add_heading(document, "3. Используемое программное обеспечение")
    add_table(
        document,
        ["Компонент", "Назначение"],
        [
            ["Ubuntu 22.04 / macOS", "Операционная система рабочей станции"],
            ["Docker Engine 20+", "Запуск контейнеров и драйвер Minikube"],
            ["Minikube v1.30+", "Локальный кластер Kubernetes"],
            ["kubectl", "Управление ресурсами кластера"],
            ["Helm 3", "Установка Gatekeeper"],
            ["Trivy", "Сканирование образов на уязвимости"],
            ["kube-bench", "Аудит конфигурации Kubernetes по CIS Benchmark"],
            ["Git", "Хранение манифестов и результатов работы"],
        ],
    )

    add_heading(document, "4. Краткое описание развернутой системы")
    add_paragraph(
        document,
        "В работе рассматривается условная распределённая ИАС из трёх подсистем. "
        "Компонент frontend имитирует приём данных и внешний вход в систему, backend выполняет "
        "аналитическую обработку, а database хранит данные в PostgreSQL. Между компонентами "
        "вводятся сетевые ограничения: frontend не должен обращаться к базе данных напрямую, "
        "доступ разрешается только по цепочке frontend → backend → database."
    )
    add_table(
        document,
        ["Namespace", "Роль", "Образ", "Профиль безопасности"],
        [
            ["frontend", "Сервис приёма данных", "nginx", "baseline"],
            ["backend", "Аналитическая обработка", "httpd:2.4", "baseline"],
            ["database", "Хранение данных", "postgres:15", "restricted"],
        ],
    )

    add_heading(document, "5. Ход выполнения работы")
    add_heading(document, "5.1 Развёртывание локального кластера", level=2)
    add_paragraph(document, "На первом этапе был запущен одновузловой кластер Minikube с драйвером Docker.")
    add_code_block(
        document,
        """
minikube start --driver=docker --memory=4096 --cpus=2
kubectl cluster-info
kubectl get nodes -o wide
        """,
    )
    add_paragraph(
        document,
        "Команда `kubectl cluster-info` подтверждает доступность управляющей плоскости, "
        "а вывод `kubectl get nodes` позволяет убедиться, что нода переведена в состояние Ready."
    )
    add_image(document, CLUSTER_IMAGE, "Рисунок 1. Состояние кластера Minikube после запуска", width_cm=16.3)

    add_heading(document, "5.2 Создание пространств имён и настройка Pod Security Admission", level=2)
    add_code_block(
        document,
        """
kubectl create ns frontend
kubectl create ns backend
kubectl create ns database

kubectl label ns frontend pod-security.kubernetes.io/enforce=baseline
kubectl label ns backend pod-security.kubernetes.io/enforce=baseline
kubectl label ns database pod-security.kubernetes.io/enforce=restricted

kubectl get ns --show-labels
        """,
    )
    add_paragraph(
        document,
        "Профиль `baseline` защищает от очевидно опасных настроек, но допускает запуск "
        "обычных приложений. Профиль `restricted` для пространства `database` усиливает требования: "
        "ограничивает привилегии контейнера, принуждает использовать безопасный security context "
        "и снижает риск компрометации базы данных."
    )
    add_image(document, NAMESPACES_IMAGE, "Рисунок 2. Пространства имён и метки Pod Security Admission", width_cm=16.3)

    add_heading(document, "5.3 Развёртывание тестовых приложений", level=2)
    add_paragraph(
        document,
        "Для моделирования архитектуры использованы три Deployment и соответствующие Service. "
        "Во все шаблоны подов сразу добавлена метка `data-classification: internal`, чтобы в дальнейшем "
        "они соответствовали политике Gatekeeper."
    )
    add_code_block(
        document,
        """
# frontend-deploy.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: frontend
spec:
  replicas: 1
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
        data-classification: internal
    spec:
      containers:
      - name: frontend
        image: nginx:latest
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: frontend
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 80
        """,
    )
    add_code_block(
        document,
        """
# backend-deploy.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: backend
spec:
  replicas: 1
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
        data-classification: internal
    spec:
      serviceAccountName: backend-sa
      containers:
      - name: backend
        image: httpd:2.4
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: backend
spec:
  selector:
    app: backend
  ports:
  - port: 80
    targetPort: 80
        """,
    )
    add_code_block(
        document,
        """
# database-deploy.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: database
  namespace: database
spec:
  replicas: 1
  selector:
    matchLabels:
      app: database
  template:
    metadata:
      labels:
        app: database
        data-classification: internal
    spec:
      securityContext:
        runAsNonRoot: true
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: database
        image: postgres:15
        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            drop: ["ALL"]
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: ias
        - name: POSTGRES_USER
          value: analyst
        - name: POSTGRES_PASSWORD
          value: analystpass
---
apiVersion: v1
kind: Service
metadata:
  name: database
  namespace: database
spec:
  selector:
    app: database
  ports:
  - port: 5432
    targetPort: 5432
        """,
    )
    add_code_block(
        document,
        """
kubectl apply -f frontend-deploy.yaml
kubectl apply -f backend-deploy.yaml
kubectl apply -f database-deploy.yaml
kubectl get pods -A
kubectl get svc -A
        """,
    )
    add_image(document, WORKLOADS_IMAGE, "Рисунок 3. Развёрнутые поды и сервисы в кластере", width_cm=16.3)

    add_heading(document, "5.4 Настройка сетевых политик", level=2)
    add_paragraph(
        document,
        "Для реализации принципа минимально необходимого сетевого доступа в пространстве `database` "
        "создана политика, разрешающая входящие соединения только от подов `backend`. "
        "Это предотвращает прямой доступ `frontend` к PostgreSQL."
    )
    add_code_block(
        document,
        """
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: db-policy
  namespace: database
spec:
  podSelector:
    matchLabels:
      app: database
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: backend
      podSelector:
        matchLabels:
          app: backend
    ports:
    - protocol: TCP
      port: 5432
        """,
    )
    add_code_block(
        document,
        """
kubectl apply -f db-network-policy.yaml
kubectl exec -n frontend deploy/frontend -- nc -vz database.database.svc.cluster.local 5432
kubectl exec -n backend deploy/backend -- nc -vz database.database.svc.cluster.local 5432
        """,
    )
    add_paragraph(
        document,
        "Ожидаемый результат проверки: из `frontend` соединение не устанавливается, а из `backend` "
        "порт 5432 доступен. Таким образом подтверждается соблюдение модели Zero Trust на межсервисном уровне."
    )
    add_image(document, NETWORK_SCHEME_IMAGE, "Рисунок 4. Схема сетевых политик между компонентами ИАС", width_cm=16.0)
    add_image(document, NETWORK_CHECK_IMAGE, "Рисунок 5. Проверка запрета frontend → database и разрешения backend → database", width_cm=16.3)

    add_heading(document, "5.5 Настройка RBAC для сервисной учётной записи", level=2)
    add_paragraph(
        document,
        "Для компонента `backend` создана отдельная сервисная учётная запись `backend-sa`, "
        "получившая только права чтения ConfigMap в своём namespace."
    )
    add_code_block(
        document,
        """
apiVersion: v1
kind: ServiceAccount
metadata:
  name: backend-sa
  namespace: backend
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: configmap-reader
  namespace: backend
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-configmaps
  namespace: backend
subjects:
- kind: ServiceAccount
  name: backend-sa
  namespace: backend
roleRef:
  kind: Role
  name: configmap-reader
  apiGroup: rbac.authorization.k8s.io
        """,
    )
    add_code_block(
        document,
        """
kubectl apply -f backend-rbac.yaml
kubectl auth can-i list configmaps --as=system:serviceaccount:backend:backend-sa -n backend
kubectl auth can-i list secrets --as=system:serviceaccount:backend:backend-sa -n backend
        """,
    )
    add_paragraph(
        document,
        "При проверке ожидается, что чтение ConfigMap разрешено, а просмотр Secret запрещён. "
        "Это демонстрирует корректную реализацию принципа наименьших привилегий."
    )
    add_image(document, RBAC_IMAGE, "Рисунок 6. Проверка полномочий сервисной учётной записи backend-sa", width_cm=16.0)

    add_heading(document, "5.6 Аудит конфигурации кластера по CIS Benchmark", level=2)
    add_code_block(
        document,
        """
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml
kubectl wait --for=condition=complete job/kube-bench --timeout=300s
kubectl logs job/kube-bench
        """,
    )
    add_paragraph(
        document,
        "Отчёт `kube-bench` содержит предупреждения и ошибки по нескольким категориям. "
        "Для локального кластера Minikube часть замечаний может быть связана со служебной конфигурацией "
        "control plane и не всегда устранима без изменения параметров запуска кластера. В отчёте рекомендуется "
        "отдельно отметить такие пункты и отделить их от реально исправимых настроек."
    )
    add_paragraph(document, "Типовые предупреждения, которые следует проанализировать и по возможности исправить:")
    add_bullet_list(
        document,
        [
            "включение анонимной аутентификации (`--anonymous-auth=false`);",
            "настройка audit log (`--audit-log-path`, политика аудита и ротация журналов);",
            "отключение профилирования API-сервера (`--profiling=false`);",
            "жёсткая настройка admission-плагинов и параметров авторизации;",
            "защита конфигурационных файлов control plane по правам доступа.",
        ],
    )
    add_paragraph(
        document,
        "В качестве примера в отчёте можно зафиксировать три исправления: отключение анонимного доступа, "
        "включение журнала аудита и отключение профилирования API-сервера. После изменения конфигурации "
        "Minikube необходимо повторно выполнить `kube-bench` и сравнить количество предупреждений."
    )
    add_image(document, KUBEBENCH_BEFORE_IMAGE, "Рисунок 7. Фрагмент отчёта kube-bench до исправления параметров API-сервера", width_cm=16.3)
    add_image(document, KUBEBENCH_AFTER_IMAGE, "Рисунок 8. Повторный запуск kube-bench после усиления конфигурации", width_cm=16.3)

    add_heading(document, "5.7 Внедрение OPA Gatekeeper", level=2)
    add_code_block(
        document,
        """
helm repo add gatekeeper https://open-policy-agent.github.io/gatekeeper/charts
helm install gatekeeper gatekeeper/gatekeeper \
  --namespace gatekeeper-system \
  --create-namespace
        """,
    )
    add_paragraph(document, "Далее создан шаблон ограничения, требующий наличие метки `data-classification` у каждого Pod.")
    add_code_block(
        document,
        """
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8srequiredlabels
spec:
  crd:
    spec:
      names:
        kind: K8sRequiredLabels
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequiredlabels

        violation[{"msg": msg, "details": {"missing_labels": missing}}] {
          provided := {label | input.review.object.metadata.labels[label]}
          required := {label | label := input.parameters.labels[_].key}
          missing := required - provided
          count(missing) > 0
          msg := sprintf("you must provide labels: %v", [missing])
        }
        """,
    )
    add_code_block(
        document,
        """
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredLabels
metadata:
  name: require-data-classification
spec:
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
  parameters:
    labels:
    - key: data-classification
        """,
    )
    add_code_block(
        document,
        """
kubectl apply -f gatekeeper-template.yaml
kubectl apply -f gatekeeper-constraint.yaml
kubectl apply -f pod-without-label.yaml
kubectl apply -f pod-with-label.yaml
        """,
    )
    add_paragraph(
        document,
        "Ожидаемое поведение: под без обязательной метки отклоняется admission-контроллером, "
        "а ресурс с меткой `data-classification: internal` создаётся успешно. Такой механизм помогает "
        "централизованно enforcing организационные политики и поддерживать комплаенс."
    )
    add_image(document, GATEKEEPER_DENIED_IMAGE, "Рисунок 9. Отклонение Pod без обязательной метки data-classification", width_cm=16.0)
    add_image(document, GATEKEEPER_ALLOWED_IMAGE, "Рисунок 10. Успешное создание Pod после добавления обязательной метки", width_cm=16.0)

    add_heading(document, "5.8 Сканирование образов при помощи Trivy", level=2)
    add_code_block(
        document,
        """
trivy image nginx:latest
trivy image httpd:2.4
trivy image postgres:15
        """,
    )
    add_paragraph(
        document,
        "Сканирование контейнерных образов позволяет заранее обнаружить критические уязвимости "
        "в базовых слоях, библиотеках и системных пакетах. Особое внимание следует уделить находкам "
        "с уровнем `CRITICAL`, особенно если они затрагивают компоненты, доступные из сети или обрабатывающие данные."
    )
    add_table(
        document,
        ["Образ", "Что проверить в отчёте Trivy", "Рекомендуемые меры"],
        [
            ["nginx:latest", "Наличие CRITICAL/CVE в пакетах базового образа", "Переход на более свежий тег, `nginx:stable-alpine` или distroless-вариант"],
            ["httpd:2.4", "Уязвимости в OpenSSL, APR и системных пакетах", "Обновление патч-версии и сокращение набора пакетов"],
            ["postgres:15", "Уязвимости в libc, openssl, perl и зависимостях", "Использование последнего патч-релиза и регулярное пересоздание образов"],
        ],
    )
    add_paragraph(document, "Дополнительные меры снижения риска:")
    add_bullet_list(
        document,
        [
            "использовать минималистичные базовые образы;",
            "исключать из контейнера лишние утилиты и пакетные менеджеры;",
            "регулярно перестраивать и пересканировать образы в CI/CD;",
            "фиксировать версии образов вместо безусловного применения тега `latest`.",
        ],
    )
    add_image(document, TRIVY_IMAGE, "Рисунок 11. Сводка сканирования образов Trivy по критическим уязвимостям", width_cm=16.0)

    add_heading(document, "6. Результаты и выводы")
    add_paragraph(
        document,
        "В ходе лабораторной работы были изучены основные практики защиты распределённой "
        "контейнеризированной ИАС: изоляция сетевого взаимодействия, разграничение полномочий "
        "сервисных учётных записей, применение Pod Security Standards, аудит конфигурации кластера "
        "на соответствие CIS Benchmark, использование policy-as-code с OPA Gatekeeper и поиск "
        "уязвимостей образов средствами Trivy."
    )
    add_paragraph(
        document,
        "Наиболее важный практический результат состоит в том, что безопасность в Kubernetes "
        "должна обеспечиваться на нескольких уровнях одновременно: сеть, идентификация, admission control, "
        "конфигурация control plane и жизненный цикл контейнерных образов. Полученные навыки применимы "
        "в реальных проектах, где требуется не только обеспечить работоспособность микросервисов, "
        "но и доказуемо выполнить требования безопасности и комплаенса."
    )

    add_heading(document, "7. Ответы на контрольные вопросы")
    add_heading(document, "1. Какие риски безопасности характерны для распределённых информационно-аналитических систем?", level=2)
    add_paragraph(
        document,
        "К основным рискам относятся несанкционированный межсервисный доступ, перехват или подмена "
        "трафика, избыточные привилегии сервисных аккаунтов, компрометация контейнерных образов, "
        "ошибки конфигурации оркестратора, утечки персональных и аналитических данных, а также отсутствие "
        "централизованного аудита и контроля соответствия."
    )

    add_heading(document, "2. Чем отличаются профили Pod Security Standards?", level=2)
    add_paragraph(
        document,
        "`privileged` практически не ограничивает запуск подов и допускает опасные настройки. "
        "`baseline` блокирует наиболее рискованные механизмы, но подходит для большинства типовых приложений. "
        "`restricted` предъявляет наиболее строгие требования: запрещает привилегированные контейнеры, "
        "ограничивает capabilities, требует безопасные параметры security context и рекомендуется для чувствительных сервисов."
    )

    add_heading(document, "3. Как Network Policies реализуют модель нулевого доверия?", level=2)
    add_paragraph(
        document,
        "NetworkPolicy позволяет явно описать, кто и по каким портам может взаимодействовать с подом. "
        "При подходе Zero Trust трафик по умолчанию считается недоверенным, поэтому разрешаются только "
        "необходимые соединения между известными источниками и целевыми сервисами."
    )

    add_heading(document, "4. Каким образом OPA Gatekeeper помогает обеспечить комплаенс?", level=2)
    add_paragraph(
        document,
        "Gatekeeper переносит организационные и нормативные требования в формализованные политики, "
        "которые автоматически проверяются при создании ресурсов. Это уменьшает влияние человеческого фактора, "
        "делает контроль единообразным и позволяет доказать соблюдение внутренних стандартов."
    )

    add_heading(document, "5. Какие категории CIS Benchmark особенно важны для защиты данных?", level=2)
    add_paragraph(
        document,
        "Наиболее критичны настройки аутентификации и авторизации, аудит действий, защита секретов, "
        "безопасность API-сервера, корректные права на конфигурационные файлы и ограничение доступа "
        "к компонентам control plane. Именно эти меры напрямую влияют на конфиденциальность и целостность данных."
    )

    add_heading(document, "6. Почему важно регулярно сканировать контейнерные образы?", level=2)
    add_paragraph(
        document,
        "Даже доверенный образ со временем устаревает и накапливает известные CVE. Регулярное сканирование "
        "позволяет вовремя выявлять критические уязвимости, планировать обновления и сокращать поверхность атаки. "
        "Минимизировать риск помогают точечные теги версий, минимальные базовые образы, удаление лишних пакетов "
        "и автоматическая проверка образов в CI/CD."
    )

    add_heading(document, "8. Примечание по заполнению отчёта")
    add_paragraph(
        document,
        "Документ содержит полностью оформленную текстовую часть и места для вставки фактических "
        "скриншотов и выводов команд. Перед сдачей рекомендуется заменить шаблонные фрагменты собственными "
        "результатами выполнения `kubectl`, `kube-bench` и `trivy`, чтобы отчёт точно соответствовал выполненной работе."
    )

    document.save(OUTPUT_DOCX)
    print(f"Created: {OUTPUT_DOCX}")


if __name__ == "__main__":
    main()
