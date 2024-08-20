.. _rest_api:

REST API
=========

The ODA REST API supports resources for SBDefinitions, SBInstances, ExecutionBlocks and Projects.
Each resource supports a POST method to create a new entity, which will fetch a new identifier from SKUID.
There are also GET and PUT method for a resource identifier to retrieve and update the entity, retrospectively.
There is also a general end point which will support PUT for multiple resources as an atomic operation.


Once deployed, the API should be available at ``<HOST>/slt/api/<MAJOR_VERSION>/<RESOURCE>`` and the Swagger UI at ``<HOST>/api/<MAJOR_VERSION>/ui``. The host depends on the environment that the server is deployed to, and may include a k8s namespace - see the README for more details. For example, to retrieve slt shift data slt-01-20200325-00001 from the staging environment, the request would be

.. code-block:: console

   $ curl -iX GET -H -d  "https://k8s.stfc.skao.int/staging-ska-oso-slt-services/slt/api/<MAJOR_VERSION>/sbds/sbd-mvp01-20200325-00001"


The resource endpoints, with the accepted requests and expected responses, are documented below:

.. openapi:: ../../../src/ska_oso_slt_services/rest/openapi/slt-openapi-v1.yaml