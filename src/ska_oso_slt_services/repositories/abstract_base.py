from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from ska_oso_slt_services.models.data_models import Shift


class ShiftRepository(ABC):
    @abstractmethod
    def get_shifts(self,shift_start:Optional[datetime],shift_end:Optional[datetime]) -> List[Shift]:
        raise NotImplementedError

    @abstractmethod
    def get_shift(self, id: str) -> Shift:
        raise NotImplementedError

class CRUDShiftRepository(ShiftRepository):
    @abstractmethod
    def create_shift(self, shift: Shift) -> Shift:
        raise NotImplementedError

    @abstractmethod
    def update_shift(self, shift: Shift) -> Shift:
        raise NotImplementedError

    @abstractmethod
    def delete_shift(self, id: str) -> bool:
        raise NotImplementedError
