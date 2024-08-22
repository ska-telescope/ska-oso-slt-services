.. _rest_api:

REST API
=========

The SLT REST API's support added for create shift, update and get shifts.
Each resource supports a POST method to create a new shift with unique shift_id.
There are also GET and PUT method for a resource identifier to retrieve and update the shift, retrospectively.

Once deployed, the API should be available at ``<HOST>/slt/api/<MAJOR_VERSION>/<RESOURCE>`` and the Swagger UI at ``<HOST>/api/<MAJOR_VERSION>/ui``.
The host depends on the environment that the server is deployed to, and may include a k8s namespace - see the README for more details. 
For example, to retrieve slt shift between shift_start and shift_end from the staging environment, the request would be

.. code-block:: console

   $ curl -iX GET -H -d  "https://k8s.stfc.skao.int/staging-ska-oso-slt-services/slt/api/<MAJOR_VERSION>/shifts?shift_start=2024-08-13T00%3A00%3A00&shift_end=2024-08-13T16%3A00%3A00"

   * Response

    .. code:: python
      [
         {
            "annotations": "Routine maintenance shift.",
            "comments": "All systems operational.",
            "created_time": "2024-08-13T12:28:39.085048Z",
            "id": 42,
            "media": [
               {
               "path": "/path/to/test_image.png",
               "type": "image"
               }
            ],
            "shift_end": "2024-08-13T12:45:00Z",
            "shift_id": "shift-20240813-42",
            "shift_logs": [
               {
               "info": {
                  "eb_id": "eb-t0001-20240813-00010",
                  "interface": "https://schema.skao.int/ska-oso-pdm-eb/0.1",
                  "metadata": {
                     "created_by": "DefaultUser",
                     "created_on": "2024-08-13T06:59:22.909729Z",
                     "last_modified_by": "DefaultUser",
                     "last_modified_on": "2024-08-13T06:59:22.909729Z",
                     "version": 1
                  },
                  "request_responses": [
                     {
                     "request": "ska_oso_scripting.functions.devicecontrol.release_all_resources",
                     "request_args": {
                        "kwargs": {
                           "subarray_id": "1"
                        }
                     },
                     "request_sent_at": "2022-09-23T15:43:53.971548Z",
                     "response": {
                        "result": "this is a result"
                     },
                     "response_received_at": "2022-09-23T15:43:53.971548Z",
                     "status": "OK"
                     },
                     {
                     "error": {
                        "detail": "this is an error"
                     },
                     "request": "ska_oso_scripting.functions.devicecontrol.scan",
                     "request_sent_at": "2022-09-23T15:43:53.971548Z",
                     "status": "ERROR"
                     }
                  ],
                  "sbd_ref": "sbd-t0001-20240812-00001",
                  "sbd_version": 1,
                  "sbi_ref": "sbi-t0001-20240812-00002",
                  "sbi_status": "Created",
                  "telescope": "ska_mid"
               },
               "log_time": "2024-08-13T12:29:24.155159Z",
               "source": "ODA"
               },
               {
               "info": {
                  "eb_id": "eb-t0001-20240813-00009",
                  "interface": "https://schema.skao.int/ska-oso-pdm-eb/0.1",
                  "metadata": {
                     "created_by": "DefaultUser",
                     "created_on": "2024-08-13T06:58:45.693863Z",
                     "last_modified_by": "DefaultUser",
                     "last_modified_on": "2024-08-13T06:58:45.693863Z",
                     "version": 1
                  },
                  "request_responses": [
                     {
                     "request": "ska_oso_scripting.functions.devicecontrol.release_all_resources",
                     "request_args": {
                        "kwargs": {
                           "subarray_id": "1"
                        }
                     },
                     "request_sent_at": "2022-09-23T15:43:53.971548Z",
                     "response": {
                        "result": "this is a result"
                     },
                     "response_received_at": "2022-09-23T15:43:53.971548Z",
                     "status": "OK"
                     },
                     {
                     "error": {
                        "detail": "this is an error"
                     },
                     "request": "ska_oso_scripting.functions.devicecontrol.scan",
                     "request_sent_at": "2022-09-23T15:43:53.971548Z",
                     "status": "ERROR"
                     }
                  ],
                  "sbd_ref": "sbd-t0001-20240812-00001",
                  "sbd_version": 1,
                  "sbi_ref": "sbi-t0001-20240812-00002",
                  "sbi_status": "Created",
                  "telescope": "ska_mid"
               },
               "log_time": "2024-08-13T12:28:49.104331Z",
               "source": "ODA"
               }
            ],
            "shift_operator": {
               "name": "John Doe"
            },
            "shift_start": "2024-08-13T12:28:39.085060Z"
         }
      ]

The SLT API endpoints, with the accepted requests and expected responses, are documented below:

.. openapi:: ../../../src/ska_oso_slt_services/rest/openapi/slt-openapi-v1.yaml
   