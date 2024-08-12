from datetime import datetime
from typing import List, Optional

from ska_oso_slt_services.models.data_models import Shift, Media
from ska_oso_slt_services.repositories.abstract_base import (
    CRUDShiftRepository,
    ShiftRepository,
)


class ShiftService:
    def __init__(
        self,
        shift_repositories: Optional[List[ShiftRepository]],
        crud_shift_repository: CRUDShiftRepository,
    ):
        self.shift_repositories = shift_repositories
        self.crud_shift_repository = crud_shift_repository

    def getShifts(
        self,
        shift_start: Optional[datetime] = None,
        shift_end: Optional[datetime] = None,
    ) -> List[Shift]:
        return self.crud_shift_repository.get_shifts(shift_start, shift_end)

    def get_shift(self, id: int) -> Shift:
        return self.crud_shift_repository.get_shift(id)
    
    def get_media(self, shift_id: int) -> Media:
        return self.crud_shift_repository.get_media(shift_id)
    
    def add_media(self, shift_id: int, media: Media) -> Media:
        return self.crud_shift_repository.add_media(shift_id, media)

    def create_shift(self, shift: Shift) -> Shift:

        created_shift = self.crud_shift_repository.create_shift(shift)
        return created_shift

    def update_shift(self, shift: Shift) -> Shift:
        updated_shift = self.crud_shift_repository.update_shift(shift)
        return updated_shift

    def delete_shift(self, id: str):
        pass
