from abc import abstractmethod
from typing import List, Optional

from ska_oso_slt_services.domain.shift_models import (
    DateQuery,
    JsonQuery,
    Shift,
    TextQuery,
    UserQuery,
)
from ska_oso_slt_services.repository.shift_repository import ShiftRepository


class EDAShiftRepository(ShiftRepository):
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
        text_query: Optional[TextQuery] = None,
        json_query: Optional[JsonQuery] = None,
    ) -> List[Shift]:
        """
        Retrieve a list of shifts within the specified start and end times.
         no end time filter is applied.
         :param user_query: Optional[UserQuery]: Query parameters for
         filtering shifts by user.
         :param date_query: Optional[DateQuery]: Query parameters for
         filtering shifts by date.
         :param text_query: Optional[TextQuery]: Query parameters for
         filtering shifts by text.
         :param json_query: Optional[JsonQuery]: Query parameters for
         filtering shifts by JSON-based criteria.


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
