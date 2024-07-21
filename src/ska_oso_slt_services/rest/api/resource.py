from datetime import datetime
from functools import wraps
from http import HTTPStatus
from typing import Callable
import logging
from flask import Response
from repository_classes.data_repository_mappings import ODASLTRepository, ODASLTLogsRepository, ODASLTImagesRepository
from pydantic_data_models.data_models import ODASLT, ODASLTLogs, ODASLTImages

LOGGER = logging.getLogger(__name__)
#Response = Tuple[Union[OSOEntity, dict], int]

odaslt_repo = ODASLTRepository()
odaslt_logs_repo = ODASLTLogsRepository()
odaslt_images_repo = ODASLTImagesRepository()


#################ODASLT################################


#GET


def get_shift_comment(record_id): #id
    odaslt_records = odaslt_repo.get_records_by_id_or_by_slt_ref(record_id=record_id)
    return odaslt_records, HTTPStatus.OK


def get_shift_comments(**kwargs): #time
    #validation logic
    validated_params = kwargs
    odaslt_records = odaslt_repo.get_records_by_shift_time(start_time=validated_params["start_time"],end_time=validated_params["start_time"])
    return odaslt_records, HTTPStatus.OK



def get_shift_comment_data_with_logs_and_images(record_id): #id
    odaslt_record_with_logs_and_images = odaslt_repo.get_records_with_logs_and_image(record_id=1721409491)
    return odaslt_record_with_logs_and_images, HTTPStatus.OK

def get_shift_comments_data_with_logs_and_images(**kwargs): #time
    # validation logic
    validated_params = kwargs

    odaslt_all_records_with_logs_and_images = odaslt_repo.get_records_by_shift_time_with_logs_and_image(start_time=validated_params["start_time"],end_time=validated_params["start_time"])
    return odaslt_all_records_with_logs_and_images,HTTPStatus.OK


#post
def post_shift_comment(): #params as it eill return id
    # validation logic
    # validated_params = kwargs

    start_time = datetime.utcnow()
    #for shift start so empty obj
    oda_slt_obj = ODASLT(shift_start=start_time)
    insert_record = odaslt_repo.insert(record=oda_slt_obj.model_dump(mode="JSON",exclude_none=True))
    print("Inserted record into tab_oda_slt",insert_record["id"],"\n\n\n")





def put_shift_comment(record_id,**kwargs): #shift comment, end
    odaslt_record = odaslt_repo.get_records_by_id_or_by_slt_ref(record_id=record_id)[0]

    #update comments and annotation
    updated_comments = f"This is my updated comment {odaslt_record['comments']}"
    oda_slt_obj = ODASLT(comments=updated_comments)
    # import pdb
    # pdb.set_trace()
    #odaslt_repo1 = odaslt_repo.update_record_by_id_or_slt_ref(record=oda_slt_obj.model_dump(mode="JSON",exclude_none=True),record_id=record_id)



    #update info
    odaslt_logs_record = odaslt_logs_repo.get_records_by_id_or_by_slt_ref(slt_ref=record_id)[0]

    info = odaslt_logs_record["info"]
    info[f"{datetime.utcnow().timestamp()}"] = {"new_info": {"key": 1}}
    oda_slt_logs_obj = ODASLTLogs(info=info)
    odaslt_logs_repo.update_record_by_id_or_slt_ref(slt_ref=record_id,record=oda_slt_logs_obj.model_dump(mode="JSON",exclude_none=True))

    #update  image
    odaslt_image_record = odaslt_images_repo.get_records_by_id_or_by_slt_ref(slt_ref=record_id)[0]
    image_path = ["/new_path/1.jpg","/new_path/2.jpg"]
    oda_slt_image_obj = ODASLTImages(image_path=image_path)

    odaslt_images_repo.update_record_by_id_or_slt_ref(slt_ref=record_id,record=oda_slt_image_obj.model_dump(mode="JSON",exclude_none=True))



def delete_comment_data_logs_and_images(record_id):
    odaslt_repo.delete_by_id(record_id=record_id)





