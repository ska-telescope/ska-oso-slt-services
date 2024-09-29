from abc import abstractmethod
from typing import List, Optional

from ska_oso_slt_services.domain.shift_models import (
    DateQuery,
    Shift,
    TextBasedQuery,
    UserQuery,
)
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
        user_query: Optional[UserQuery] = None,
        date_query: Optional[DateQuery] = None,
        text_based_query: Optional[TextBasedQuery] = None,
    ) -> List[Shift]:
        """
        Retrieve a list of shifts within the specified start and end times.

        :param shift_start: Optional[datetime]: The start time to filter shifts. If None
        , no start time filter is applied.
        :param shift_end: Optional[datetime]: The end time to filter shifts. If None,
         no end time filter is applied.

        :returns: A list of Shift objects that fall within the specified time range.

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
