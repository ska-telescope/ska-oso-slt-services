import logging
from datetime import datetime
from functools import wraps
from http import HTTPStatus
from typing import Optional, Callable, Tuple, Union
import time
from deepdiff import DeepDiff
from pydantic import ValidationError
from ska_db_oda.domain.query import QueryParams
from ska_db_oda.rest.api.resources import get_qry_params, error_response
from ska_db_oda.unit_of_work.postgresunitofwork import PostgresUnitOfWork

from ska_oso_slt_services.data_access.postgres_data_acess import PostgresDataAccess, PostgresConnection
from ska_oso_slt_services.models.data_models import Shift, ShiftLogs
from ska_oso_slt_services.repositories.postgres_shift_repository import PostgresShiftRepository
from ska_oso_slt_services.services.shift_service import ShiftService


LOGGER = logging.getLogger(__name__)
Response = Tuple[Union[dict, list], int]

shift_repository = PostgresShiftRepository()
shift_service = ShiftService(crud_shift_repository=shift_repository,shift_repositories=None)


uow = PostgresUnitOfWork(PostgresConnection().get_connection())

dummy_data_insert = {
  "shift_start": "2024-07-01T08:00:00",
  "shift_end": "2024-07-01T16:00:00",
  "shift_operator": {
    "name": "John Doe"
  },
  "shift_logs": [
    {
      "info": {"detail": "Initial log entry."},
      "source": "system",
      "log_time": "2024-07-01T08:30:00"
    }
  ],
  "media": [
    {
      "type": "image",
      "path": "/path/to/image1.png"
    }
  ],
  "annotations": "Routine maintenance shift.",
  "comments": "All systems operational.",
  "created_by": "admin",
  "created_time": "2024-07-01T07:50:00",
  "last_modified_by": "admin",
  "last_modified_time": "2024-07-01T15:00:00"
}


dummy_data_update = {
    "id": 12,
  "shift_start": "2024-07-01T08:00:00",
  "shift_end": "2024-07-01T16:00:00",
  "shift_operator": {
    "name": "John Doe"
  },
  "shift_logs": [
    {
      "info": {"detail": "Initial log entry."},
      "source": "system",
      "log_time": "2024-07-01T08:30:00"
    }
  ],
  "media": [
    {
      "type": "image",
      "path": "/path/to/image1.png"
    },
{
      "type": "image",
      "path": "/path/to/image2.png"
    }

  ],
  "annotations": "UpdatedRoutine maintenance shift.",
  "comments": "Updated All systems operational.",
  "created_by": "admin",
  "created_time": "2024-07-01T07:50:00",
  "last_modified_by": "admin",
  "last_modified_time": "2024-07-01T15:00:00"
}



def error_handler(api_fn: Callable[[str], Response]) -> Callable[[str], Response]:
    """
    A decorator function to catch general errors and wrap in the correct HTTP
    response

    :param api_fn: A function which accepts an entity identifier and returns
    an HTTP response
    """

    @wraps(api_fn)
    def wrapper(*args, **kwargs):
        try:
            LOGGER.debug(
                "Request to %s with args: %s and kwargs: %s", api_fn, args, kwargs
            )
            return api_fn(*args, **kwargs)
        except KeyError as err:

            return {"detail": str(err.args[0])}, HTTPStatus.NOT_FOUND

        except (ValueError, ValidationError) as e:
            LOGGER.exception(
                "ValueError occurred when adding entity, likely some semantic"
                " validation failed"
            )

            return error_response(e, HTTPStatus.UNPROCESSABLE_ENTITY)

        except Exception as e:
            LOGGER.exception(
                "Exception occurred when calling the API function %s", api_fn
            )
            return error_response(e)

    return wrapper



def get_shifts(shift_start:Optional[str]=None, shift_end:Optional[str]=None):

  
    shift_start = datetime.fromisoformat(shift_start) if shift_start else None
    shift_end = datetime.fromisoformat(shift_end) if shift_end else None

    shifts = shift_service.getShifts(shift_start, shift_end)
    return [shift.model_dump(mode="JSON") for shift in shifts], HTTPStatus.OK



def get_shift(shift_id):
    # Fetch shift data using the service layer
    shift = shift_service.get_shift(id=shift_id)
    if shift is None:
        return {"error": "Shift not found"}, 404
    else:
        return shift.model_dump(mode="JSON"),HTTPStatus.OK


def create_shift():
    #data = request.get_json()
    #data = dummy_data_insert
    data = {}
    try:
        shift = Shift(**data)
    except ValidationError as e:
        return {"errors": e.errors()}, HTTPStatus.BAD_REQUEST

    created_shift = shift_service.create_shift(shift)
    return created_shift.model_dump(mode="JSON"), HTTPStatus.CREATED


def update_shift(**kwargs):
    #data = request.get_json()
    data = dummy_data_update
    try:
        shift = Shift(**data)
    except ValidationError as e:
        return {"errors": e.errors()}, HTTPStatus.BAD_REQUEST

    updated_shift = shift_service.update_shift(shift)
    return updated_shift.model_dump(mode="JSON"), HTTPStatus.CREATED


# def update_info_for_shift(shift_id):
#     shift = shift_service.get_shift(id=shift_id)
#     if shift is None:
#         return {"error": "Shift not found"}, 404
#     current_info_in_db =  shift.shift_logs...
#     params_dict = {'match_type': 'equals', 'created_after': '2022-03-28T15:43:53.971548+00:00'}
#     new_info_in_db = get_eb_sbi_status(params_dict)
#     #compare old and new data
#     #and if new data found then update and update record



def get_eb_sbi_status(**kwargs):
    if not isinstance(maybe_qry_params := get_qry_params(kwargs), QueryParams):
        return maybe_qry_params

    with uow:
        ebs = uow.ebs.query(maybe_qry_params)

        info = {}
        for eb in ebs:
            # import pdb
            #  pdb.set_trace()
            info_single_record = eb.model_dump(mode="json")
            sbi_current_status = uow.sbis_status_history.get(entity_id=eb.sbi_ref).model_dump(mode="json")["current_status"]
            info_single_record["sbi_status"] = sbi_current_status
            #info_single_record["source"] = "ODA"
            info_single_record["request_responses"][:] = [record for record in info_single_record["request_responses"] if record.get('status') in ('observed', 'failed',)]
            info[eb.eb_id] = info_single_record
    return info


def update_info_for_shift(shift_id: int, poll_interval: int = 5):

   # last_check_time = datetime.utcnow()  # Keep track of the last check time
    last_check_time = datetime(2024, 7, 1, 12, 0, 0)  # July 1, 2024, 12:00 PM UTC

    while True:
        shift = shift_service.get_shift(id=shift_id)
        if shift is None:
            print("Shift not found")
            return {"error": "Shift not found"}, 404

        current_info_in_db = {log.info.get("eb_id"): log for log in shift.shift_logs} if shift.shift_logs else {}


        params_dict = {
           # 'created_after': last_check_time.isoformat(),
            'last_modified_after': last_check_time.isoformat(),

            # 'created_before': some_datetime.isoformat(),
            # 'last_modified_before': some_datetime.isoformat(),
        }
        new_info = get_eb_sbi_status(**params_dict)


        params_dict = {
             'created_after': last_check_time.isoformat(),
            #'last_modified_after': last_check_time.isoformat(),
            # 'created_before': some_datetime.isoformat(),
            # 'last_modified_before': some_datetime.isoformat(),
        }
        new_info1 = get_eb_sbi_status(**params_dict)

        new_info.update(new_info1)
        import pdb
        pdb.set_trace()
        print("--------",type(new_info))

        last_check_time = datetime.utcnow()


        diff = DeepDiff(current_info_in_db, new_info, ignore_order=True)

        if diff:
            print("Differences found, updating shift logs...")

           # import pdb
           #  pdb.set_trace()
            for eb_id, new_data in new_info.items():
                if eb_id in current_info_in_db:

                    current_log = current_info_in_db[eb_id]
                    current_log.info.update(new_data)
                    current_log.log_time = datetime.now()
                else:

                    new_log = ShiftLogs(info=new_data, log_time=datetime.now(), source="ODA")
                    if shift.shift_logs:
                        shift.shift_logs.append(new_log)
                    else:
                        shift.shift_logs = [new_log]


            shift_service.update_shift(shift)

        else:
            print("No new data found")

        #demo polling
        time.sleep(poll_interval)




if __name__ == "__main__":
    #print(create_shift())
    print(get_shifts())
    #print(update_shift())
    #print(get_shifts())
    #params_dict = {'match_type': 'equals', 'created_after': '2022-03-28T15:43:53.971548+00:00'}
    #print(get_eb_sbi_status(**params_dict))
    #print(update_info_for_shift())
    #print(update_info_for_shift(shift_id=15))
