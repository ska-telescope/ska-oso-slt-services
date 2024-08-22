============================
Polling ODA Log Status Data
============================

The initial version of the SLT (Shift Log Tool) provided support for fetching observation execution related logs 
from the ODA e.g. success or failure of EB (Execution Block). 

A function named ``updated_shift_log_info`` was created to facilitate this process.

The ``updated_shift_log_info`` function takes a ``current_shift_id`` as an argument, 
which is the unique identifier of the shift for which log data needs to be fetched.

This function continuously synchronizes log data from the ODA system for the specified shift. It creates a background thread that periodically polls the ODA system for new log data.

Implementation Details
------------------------

The current implementation of the ``updated_shift_log_info`` function follows a background thread-based approach 
to poll data from the ODA system. The fetched log data is then processed and stored in the ODA.


.. code-block:: console

   $ updated_shift_log_info(current_shift_id)
   
   * Response

    .. code:: python
        {
            "eb-t0001-20240820-00018": {
                "eb_id": "eb-t0001-20240820-00018",
                "sbd_ref": "sbd-t0001-20240812-00001",
                "sbi_ref": "sbi-t0001-20240812-00002",
                "metadata": {
                "version": 1,
                "created_by": "DefaultUser",
                "created_on": "2024-08-20T13:33:43.794785Z",
                "last_modified_by": "DefaultUser",
                "last_modified_on": "2024-08-20T13:33:43.794785Z"
                },
                "interface": "https://schema.skao.int/ska-oso-pdm-eb/0.1",
                "telescope": "ska_mid",
                "sbd_version": 1,
                "request_responses": [
                {
                    "status": "OK",
                    "request": "ska_oso_scripting.functions.devicecontrol.assign_resource",
                    "response": {
                    "result": "this is a result"
                    },
                    "request_args": {
                    "kwargs": {
                        "subarray_id": "1"
                    }
                    },
                    "request_sent_at": "2022-09-23T15:43:53.971548Z",
                    "response_received_at": "2022-09-23T15:43:53.971548Z"
                },
                {
                    "status": "ok",
                    "request": "ska_oso_scripting.functions.devicecontrol.configure",
                    "response": {
                    "result": "this is a result"
                    },
                    "request_sent_at": "2022-09-23T15:43:53.971548Z"
                }
                ],
                "sbi_status": "executing"
            }
        }