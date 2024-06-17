#
# CAR_OCI_REGISTRY_HOST, CAR_OCI_REGISTRY_USERNAME and PROJECT_NAME are combined to define
# the Docker tag for this project. The definition below inherits the standard
# value for CAR_OCI_REGISTRY_HOST (=artefact.skao.int) and overwrites
# CAR_OCI_REGISTRY_USERNAME and PROJECT_NAME to give a final Docker tag of
# artefact.skao.int/ska-oso-slt-services
#
PROJECT = ska-oso-slt-services
KUBE_NAMESPACE ?= ska-oso-slt-services
KUBE_HOST ?= $(shell minikube ip)
RELEASE_NAME ?= test

IMAGE_TO_TEST = $(CAR_OCI_REGISTRY_HOST)/$(strip $(OCI_IMAGE)):$(VERSION)
K8S_CHART ?= ska-oso-slt-services-umbrella
K8S_CHARTS ?= ska-oso-slt-services $(K8S_CHART)
HELM_CHART ?= ska-oso-slt-services-umbrella
UMBRELLA_CHART_PATH ?= charts/$(HELM_CHART)/
MINIKUBE ?= true ## Minikube or not

# Set sphinx documentation build to fail on warnings (as it is configured
# in .readthedocs.yaml as well)
DOCS_SPHINXOPTS ?= -W --keep-going

POSTGRES_HOST ?= $(RELEASE_NAME)-postgresql
ADMIN_POSTGRES_PASSWORD ?= secretpassword ## Password for the "postgres" admin user

# unset defaults so settings in pyproject.toml take effect
PYTHON_SWITCHES_FOR_BLACK =
PYTHON_SWITCHES_FOR_ISORT =
PYTHON_SWITCHES_FOR_PYLINT =

# Restore Black's preferred line length which otherwise would be overridden by
# System Team makefiles' 79 character default
PYTHON_LINE_LENGTH = 88

# include OCI Images support
include .make/oci.mk

# include k8s support
include .make/k8s.mk

# include Helm Chart support
include .make/helm.mk

# Include Python support
include .make/python.mk

# include raw support
include .make/raw.mk

# include core make support
include .make/base.mk

# include your own private variables for custom deployment configuration
-include PrivateRules.mak

CI_JOB_ID ?= local##pipeline job id
CLUSTER_DOMAIN ?= cluster.local## Domain used for naming Tango Device Servers
K8S_TEST_RUNNER = test-runner-$(CI_JOB_ID)##name of the pod running the k8s-test

# Single image in root of project
OCI_IMAGES = ska-oso-slt-services

POSTGRES_PARAMS = --set postgresql.primary.persistence.storageClass=standard

ifneq ($(MINIKUBE),)
ifneq ($(MINIKUBE),true)
POSTGRES_PARAMS = --set postgresql.primary.persistence.storageClass=nfss1
endif
endif

K8S_CHART_PARAMS = 	--set postgresql.auth.postgresPassword=$(ADMIN_POSTGRES_PASSWORD) \
	--set postgresql.primary.initdb.password=$(ADMIN_POSTGRES_PASSWORD) \
	--set pgadmin4.serverDefinitions.servers.firstServer.Host=$(POSTGRES_HOST) \
	$(POSTGRES_PARAMS)

# For the test, dev and integration environment, use the freshly built image in the GitLab registry
ENV_CHECK := $(shell echo $(CI_ENVIRONMENT_SLUG) | egrep 'test|dev|integration')
ifneq ($(ENV_CHECK),)
K8S_CHART_PARAMS += --set ska-oso-slt-services.rest.image.tag=$(VERSION)-dev.c$(CI_COMMIT_SHORT_SHA) \
	--set ska-oso-slt-services.rest.image.registry=$(CI_REGISTRY)/ska-telescope/db/ska-oso-slt-services
endif

# For the staging environment, make k8s-install-chart-car will pull the chart from CAR. We also want to use a PV
STAGING_ENV_CHECK := $(shell echo $(CI_ENVIRONMENT_SLUG) | egrep staging)
ifneq ($(STAGING_ENV_CHECK),)
K8S_CHART_PARAMS += --set postgresql.primary.persistence.enabled=true
endif

# Set cluster_domain to minikube default (cluster.local) in local development
# (CI_ENVIRONMENT_SLUG should only be defined when running on the CI/CD pipeline)
ifeq ($(CI_ENVIRONMENT_SLUG),)
K8S_CHART_PARAMS += --set global.cluster_domain="cluster.local"
endif

PYTHON_VARS_AFTER_PYTEST = -m 'not post_deployment'

ifeq ($(strip $(firstword $(MAKECMDGOALS))),k8s-test)
PYTHON_VARS_BEFORE_PYTEST = POSTGRES_HOST=$(POSTGRES_HOST) ADMIN_POSTGRES_PASSWORD=$(ADMIN_POSTGRES_PASSWORD) KUBE_NAMESPACE=$(KUBE_NAMESPACE) KUBE_HOST=$(KUBE_HOST)
PYTHON_VARS_AFTER_PYTEST := -m 'post_deployment' --disable-pytest-warnings 
endif

rest: ## start SLT REST server
	docker run --rm -p 5000:5000 --name=$(PROJECT_NAME) $(IMAGE_TO_TEST) gunicorn --chdir src \
		--bind 0.0.0.0:5000 --logger-class=ska_oso_slt_services.rest.wsgi.UniformLogger --log-level=$(LOG_LEVEL) ska_oso_slt_services.rest.wsgi:app

diagrams:  ## recreate PlantUML diagrams whose source has been modified
	@for i in $$(git diff --name-only -- '*.puml'); \
	do \
		echo "Recreating $${i%%.*}.png"; \
		cat $$i | docker run --rm -i think/plantuml -tsvg $$i > $${i%%.*}.svg; \
	done

# override python.mk python-pre-test target
python-pre-test:
	@echo "python-pre-test: running with: $(PYTHON_VARS_BEFORE_PYTEST) $(PYTHON_RUNNER) pytest $(PYTHON_VARS_AFTER_PYTEST) \
	 --cov=src --cov-report=term-missing --cov-report xml:build/reports/code-coverage.xml --junitxml=build/reports/unit-tests.xml $(PYTHON_TEST_FILE)"

k8s-pre-test: python-pre-test

k8s-pre-template-chart: k8s-pre-install-chart

requirements: ## Install Dependencies
	poetry install

dev-up: K8S_CHART_PARAMS += --set ska-oso-slt-services.rest.image.tag=$(VERSION) --set ska-oso-slt-services.rest.backend.type=filesystem
dev-up: k8s-namespace k8s-install-chart k8s-wait ## bring up developer deployment

dev-down: k8s-uninstall-chart k8s-delete-namespace  ## tear down developer deployment

# The docs build fails unless the ska-oso-slt-services package is installed locally as importlib.metadata.version requires it.
docs-pre-build:
	poetry install --only-root

# install helm plugin from https://github.com/helm-unittest/helm-unittest.git
k8s-chart-test:
	mkdir -p charts/build; \
	helm unittest charts/ska-oso-slt-services/ --with-subchart \
		--output-type JUnit --output-file charts/build/chart_template_tests.xml

.PHONY: $(MAKECMDGOALS) 