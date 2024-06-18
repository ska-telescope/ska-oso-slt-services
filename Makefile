
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

# include makefile to pick up the standard Make targets from the submodule

-include .make/helm.mk
-include .make/base.mk
-include .make/oci.mk
-include .make/k8s.mk
-include .make/python.mk

# Set sphinx documentation build to fail on warnings (as it is configured
# in .readthedocs.yaml as well)
DOCS_SPHINXOPTS ?= -W --keep-going

docs-pre-build:
	poetry config virtualenvs.create false
	poetry install --no-root --only docs

.PHONY: docs-pre-build

IMAGE_TO_TEST = $(CAR_OCI_REGISTRY_HOST)/$(strip $(OCI_IMAGE)):$(VERSION)

# For the test, dev and integration environment, use the freshly built image in the GitLab registry
ENV_CHECK := $(shell echo $(CI_ENVIRONMENT_SLUG) | egrep 'test|dev|integration')
ifneq ($(ENV_CHECK),)
K8S_CHART_PARAMS = --set ska-oso-slt-services.rest.image.tag=$(VERSION)-dev.c$(CI_COMMIT_SHORT_SHA) \
	--set ska-oso-slt-services.rest.image.registry=$(CI_REGISTRY)/ska-telescope/ost/ska-oso-slt-services
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

# Set python-test make target to run unit tests and not the component tests
PYTHON_TEST_FILE = tests/unit/


# include your own private variables for custom deployment configuration
-include PrivateRules.mak

REST_POD_NAME=$(shell kubectl get pods -o name -n $(KUBE_NAMESPACE) -l app=ska-oso-slt-services,component=rest | cut -c 5-)

rest: ## start SLT REST server
	docker run --rm -p 5000:5000 --name=$(PROJECT_NAME) $(IMAGE_TO_TEST) gunicorn --chdir src \
		--bind 0.0.0.0:5000 --logger-class=ska_oso_slt_services.rest.wsgi.UniformLogger --log-level=$(LOG_LEVEL) ska_oso_slt_services.rest.wsgi:app

# install helm plugin from https://github.com/helm-unittest/helm-unittest.git
k8s-chart-test:
	mkdir -p charts/build; \
	helm unittest charts/ska-oso-slt-services/ --with-subchart \
		--output-type JUnit --output-file charts/build/chart_template_tests.xml

dev-up: K8S_CHART_PARAMS = \
	--set ska-oso-slt-services.rest.image.tag=$(VERSION) \
	--set ska-oso-slt-services.rest.ingress.enabled=true
dev-up: k8s-namespace k8s-install-chart k8s-wait ## bring up developer deployment

dev-down: k8s-uninstall-chart k8s-delete-namespace  ## tear down developer deployment

