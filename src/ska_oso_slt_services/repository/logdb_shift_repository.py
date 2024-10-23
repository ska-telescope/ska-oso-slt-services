from abc import abstractmethod
from typing import List, Optional

from ska_oso_slt_services.domain.shift_models import MatchType, SbiEntityStatus, Shift
from ska_oso_slt_services.repository.shift_repository import ShiftRepository


class LogDBShiftRepository(ShiftRepository):
    """
    Concrete implementation of the ShiftRepository interface.

    This class provides a concrete implementation of the ShiftRepository interface
    using a database (e.g., PostgreSQL) as the data storage mechanism.
    """

    @abstractmethod
    def get_shifts(
        self,
        shift: Optional[Shift] = None,
        match_type: Optional[MatchType] = None,
        entity_status: Optional[SbiEntityStatus] = None,
    ) -> List[Shift]:
        """
        Retrieve a list of shifts based on specified filters.

        :param shift: Filter shifts by the provided shift object.
        :param match_type: Filter shifts by the provided match type.
        :param entity_status: Filter shifts by the provided entity status.

        :returns: A list of Shift objects matching the specified filters.

        :raises: NotImplementedError if the method is not implemented by a subclass.
        """
        raise NotImplementedError

    @abstractmethod
    def get_shift(self, shift_id: str) -> Shift:
        """
        Retrieve a shift by its SID.

        :param shift_id: The SID of the shift to retrieve.

        :returns: A Shift object with the specified SID.

        :raises: NotImplementedError if the method is not implemented by a subclass.
        """
        raise NotImplementedError
