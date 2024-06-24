import os
from importlib.metadata import version
from typing import Any, Dict

import prance
from connexion import App

KUBE_NAMESPACE = os.getenv("KUBE_NAMESPACE", "ska-oso-slt-services")
SLT_MAJOR_VERSION = version("ska-oso-slt-services").split(".")[0]
API_PATH = f"{KUBE_NAMESPACE}/slt/api/v{SLT_MAJOR_VERSION}"


# There is a (another) issue with Connexion where it cannot validate
# against a spec with polymorphism,
# As a quick has, this basically turns off the validation
class CustomRequestBodyValidator:
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, function):
        return function


# Resolves the $ref in the OpenAPI spec before it is used by Connexion,
# as Connexion can't parse them - see https://github.com/spec-first/connexion/issues/967
def get_openapi_spec() -> Dict[str, Any]:
    cwd, _ = os.path.split(__file__)
    path = os.path.join(cwd, "./openapi/slt-openapi-v1.yaml")
    parser = prance.ResolvingParser(path, lazy=True, strict=True)
    parser.parse()
    spec = parser.specification
    return spec


def init_app(open_api_spec=None):
    """
    Initialise the SLT REST application.

    Resolving the spec is relatively time-consuming, so allow a single
    spec to be injected to all the test app instances to speed up the unit tests
    """
    if open_api_spec is None:
        open_api_spec = get_openapi_spec()

    validator_map = {
        "body": CustomRequestBodyValidator,
    }
    connexion = App(__name__, specification_dir="openapi/")
    connexion.add_api(
        open_api_spec,
        # The base path includes the namespace which is known at runtime
        # to avoid clashes in deployments, for example in CICD
        base_path=f"/{API_PATH}",
        arguments={"title": "OpenAPI SLT"},
        validator_map=validator_map,
        pythonic_params=True,
    )

    app = connexion.app

    return app
