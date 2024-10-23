Shift Log Tool Services
================================

The Shift log Tool Services is the server component of the
Shift Log Tool. It provides the web services used by the
Shift Log Tool client to read and investigate stored
shift log data.

# Quick start
To clone this repository, run

```
git clone --recurse-submodules git@gitlab.com:ska-telescope/oso/ska-oso-slt-services.git
```

To refresh the GitLab Submodule, execute below commands:

```
git submodule update --recursive --remote
git submodule update --init --recursive
```

### Build and test

Install dependencies with Poetry and activate the virtual environment

```
poetry install
poetry shell
```

To build a new Docker image for the OET, run

```
make oci-build
```

Execute the test suite and lint the project with:

```
make python-test
make python-lint
```

To run a helm chart unit tests to verify helm chart configuration:

```
helm plugin install https://github.com/helm-unittest/helm-unittest.git
make k8s-chart-test
```

### Deploy to Kubernetes

Install the Helm umbrella chart into a Kubernetes cluster with ingress enabled:

```
make k8s-install-chart
```

The Swagger UI should be available external to the cluster at `http://<KUBE_HOST>/<KUBE_NAMESPACE>/slt/api/v0/ui/` and the API accesible via the same URL.

If using minikube, `KUBE_HOST` can be found by running `minikube ip`. 
`KUBE_NAMESPACE` is the namespace the chart was deployed to, likely `ska-oso-slt-services`


To uninstall the chart, run

```
make k8s-uninstall-chart
```

# Deployments from CICD

### Deploying to non-production environments

There are 3 different environments which are defined through the standard pipeline templates. They need to be manually triggered in the Gitlab UI.

1. `dev` - a temporary (4 hours) deployment from a feature branch, using the artefacts built in the branch pipeline
2. `integration` - a permanent deployment from the main branch, using the latest version of the artefacts built in the main pipeline
3. `staging` - a permanent deployment of the latest published artefact from CAR

To find the URL for the environment, see the 'info' job of the CICD pipeline stage, which should output the URL alongside the status of the Kubernetes pods.
Generally the API URL should be available at  `https://k8s.stfc.skao.int/$KUBE_NAMESPACE/slt/api/v0`


## Fast API
To start the Fast API server run the following command in a terminal bash prompt

```
fastapi dev src/ska_oso_slt_services/app.py
```


# Documentation

[![Documentation Status](https://readthedocs.org/projects/ska-telescope-ska-oso-slt-services/badge/?version=latest)](https://developer.skao.int/projects/ska-oso-slt-services/en/latest/?badge=latest)

To build the html version of the documentation, start 
from the root directory and first install the dependency using 
``poetry install --only docs`` and then type ``make docs-build html``. Read the documentation by pointing your browser
at ``docs/build/html/index.html``.
