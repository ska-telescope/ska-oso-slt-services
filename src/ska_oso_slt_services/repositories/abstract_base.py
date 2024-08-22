from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from ska_oso_slt_services.models.data_models import Media, Shift


class ShiftRepository(ABC):
    """
    Abstract base class for a Shift Repository.

    This class defines the interface for retrieving shift data from a data source.
    Any implementation of this class must provide concrete methods for the specified
    abstract methods.
    """

    @abstractmethod
    def get_shifts(
        self, shift_start: Optional[datetime], shift_end: Optional[datetime]
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
    def update_shift(self, shift: Shift) -> Shift:
        """
        Update an existing shift.

        :param shift: The Shift object to update.

        :returns: The updated Shift object.

        :raises: NotImplementedError if the method is not implemented by a subclass.
        """
        raise NotImplementedError

    @abstractmethod
    def delete_shift(self, sid: str) -> bool:
        """
        Delete a shift by its SID.

        :param sid: The SID of the shift to delete.

        :returns: True if the shift was deleted successfully, False otherwise.

        :raises: NotImplementedError if the method is not implemented by a subclass.
        """
        raise NotImplementedError

    @abstractmethod
    def get_media(self, shift_id: str) -> List[Media]:
        """
        Retrieve a list of media associated with a shift.

        :param sid: The SID of the shift to retrieve media for.

        :returns: A list of Media objects associated with the specified shift.

        :raises: NotImplementedError if the method is not implemented by a subclass.
        """
        raise NotImplementedError

    @abstractmethod
    def add_media(self, shift_id: str, media: Media) -> bool:
        """
        Add media to a shift.

        :param sid: The SID of the shift to add media to.
        :param media: The Media object to add.

        :returns: True if the media was added successfully, False otherwise.

        :raises: NotImplementedError if the method is not implemented by a subclass.
        """
        raise NotImplementedError
