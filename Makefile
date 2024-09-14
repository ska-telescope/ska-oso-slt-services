#
# CAR_OCI_REGISTRY_HOST, CAR_OCI_REGISTRY_USERNAME and PROJECT_NAME are combined to define
# the Docker tag for this project. The definition below inherits the standard
# value for CAR_OCI_REGISTRY_HOST (=artefact.skao.int) and overwrites
# PROJECT_NAME to give a final Docker tag of artefact.skao.int/ska-oso-slt-services
#
CAR_OCI_REGISTRY_HOST ?= artefact.skao.int
CAR_OCI_REGISTRY_USERNAME ?= ska-telescope
PROJECT_NAME = ska-oso-slt-services
KUBE_NAMESPACE ?= ska-oso-slt-services
RELEASE_NAME ?= test

# Set sphinx documentation build to fail on warnings (as it is configured
# in .readthedocs.yaml as well)
DOCS_SPHINXOPTS ?= -W --keep-going

IMAGE_TO_TEST = $(CAR_OCI_REGISTRY_HOST)/$(strip $(OCI_IMAGE)):$(VERSION)
K8S_CHART = ska-oso-slt-services-umbrella

POSTGRES_HOST ?= $(RELEASE_NAME)-postgresql
K8S_CHART_PARAMS += \
  --set ska-db-slt-umbrella.pgadmin4.serverDefinitions.servers.firstServer.Host=$(POSTGRES_HOST)

# For the test, dev and integration environment, use the freshly built image in the GitLab registry
ENV_CHECK := $(shell echo $(CI_ENVIRONMENT_SLUG) | egrep 'test|dev|integration')
ifneq ($(ENV_CHECK),)
K8S_CHART_PARAMS += --set ska-oso-slt-services.rest.image.tag=$(VERSION)-dev.c$(CI_COMMIT_SHORT_SHA) \
	--set ska-oso-slt-services.rest.image.registry=$(CI_REGISTRY)/ska-telescope/oso/ska-oso-slt-services
endif

# Set cluster_domain to minikube default (cluster.local) in local development
# (CI_ENVIRONMENT_SLUG should only be defined when running on the CI/CD pipeline)
ifeq ($(CI_ENVIRONMENT_SLUG),)
K8S_CHART_PARAMS += --set global.cluster_domain="cluster.local"
endif

# For the staging environment, make k8s-install-chart-car will pull the chart from CAR so we do not need to
# change any values
ENV_CHECK := $(shell echo $(CI_ENVIRONMENT_SLUG) | egrep 'staging')
ifneq ($(ENV_CHECK),)
endif

# unset defaults so settings in pyproject.toml take effect
PYTHON_SWITCHES_FOR_BLACK =
PYTHON_SWITCHES_FOR_ISORT =
PYTHON_SWITCHES_FOR_PYLINT =

# Restore Black's preferred line length which otherwise would be overridden by
# System Team makefiles' 79 character default
PYTHON_LINE_LENGTH = 88

# Set the k8s test command run inside the testing pod to only run the component
# tests (no k8s pod deployment required for unit tests)

# Set python-test make target to run unit tests and not the component tests
PYTHON_TEST_FILE = tests/unit/

# include makefile to pick up the standard Make targets from the submodule
-include .make/base.mk
-include .make/python.mk
-include .make/oci.mk
-include .make/k8s.mk

-include .make/helm.mk

# include your own private variables for custom deployment configuration
-include PrivateRules.mak

REST_POD_NAME=$(shell kubectl get pods -o name -n $(KUBE_NAMESPACE) -l app=ska-oso-slt-services,component=rest | cut -c 5-)


MINIKUBE_NFS_SHARES_ROOT ?=


dev-up: K8S_CHART_PARAMS = \
	--set ska-oso-slt-services.rest.image.tag=$(VERSION) \
	--set ska-oso-slt-services.rest.ingress.enabled=true
dev-up: k8s-namespace k8s-install-chart k8s-wait ## bring up developer deployment

dev-down: k8s-uninstall-chart k8s-delete-namespace  ## tear down developer deployment

# The docs build fails unless the ska-oso-slt-services package is installed locally as importlib.metadata.version requires it.
docs-pre-build:
	poetry install --only-root
