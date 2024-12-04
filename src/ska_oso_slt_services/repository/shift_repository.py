from abc import ABC, abstractmethod
from typing import List, Optional

from ska_oso_slt_services.domain.shift_models import MatchType, SbiEntityStatus, Shift


class ShiftRepository(ABC):
    """
    Abstract base class for a Shift Repository.

    This class defines the interface for retrieving shift data from a data source.
    Any implementation of this class must provide concrete methods for the specified
    abstract methods.
    """

    @abstractmethod
    def get_shifts(
        self,
        shift: Optional[Shift] = None,
        match_type: Optional[MatchType] = None,
        entity_status: Optional[SbiEntityStatus] = None,
    ) -> List[Shift]:
        """
        Retrieve a list of shifts based on the provided filters.

        :param shift: The shift object to filter by.
        :param match_type: The match type to filter by.
        :param entity_status: The entity status to filter by.

        :returns: A list of Shift objects matching the provided filters.

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


class CRUDShiftRepository(ShiftRepository):
    """
    Abstract base class for a CRUD Shift Repository.

    This class defines the interface for creating, updating, and deleting shift data.
    Any implementation of this class must provide concrete methods for the specified
    abstract methods.
    """

    @abstractmethod
    def create_shift(self, shift: Shift) -> Shift:
        """
        Create a new shift.

        :param shift: The Shift object to create.

        :returns: The created Shift object.

        :raises: NotImplementedError if the method is not implemented by a subclass.
        """
        raise NotImplementedError

    @abstractmethod
    def update_shift(self, shift_id, shift: Shift) -> Shift:
        """
        Update an existing shift.

        :param shift: The Shift object to update.

        :returns: The updated Shift object.

        :raises: NotImplementedError if the method is not implemented by a subclass.
        """
        raise NotImplementedError

    @abstractmethod
    def delete_shift(self, shift_id: str) -> bool:
        """
        Delete a shift by its SID.

        :param shift_id: The SID of the shift to delete.

        :returns: True if the shift was deleted successfully, False otherwise.

        :raises: NotImplementedError if the method is not implemented by a subclass.
        """
        raise NotImplementedError
