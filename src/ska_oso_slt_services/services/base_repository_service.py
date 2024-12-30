from typing import Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel, Field

from ska_oso_slt_services.common.metadata_mixin import get_latest_metadata
from ska_oso_slt_services.domain.shift_models import (
    EntityFilter,
    MatchType,
    Metadata,
    SbiEntityStatus,
    Shift,
    ShiftAnnotation,
    ShiftComment,
    ShiftLogComment,
)
from ska_oso_slt_services.repository.postgres_shift_repository import (
    CRUDShiftRepository,
    PostgresShiftRepository,
)
from ska_oso_slt_services.repository.shift_repository import ShiftRepository


class BaseRepositoryService(BaseModel):
    """
    Base class for services that manage repositories with PostgreSQL requirement.
    """

    shift_repositories: List[ShiftRepository] = Field(default_factory=list)
    crud_shift_repository: Optional[CRUDShiftRepository] = None

    def __init__(self, repositories: Optional[List[Type[ShiftRepository]]] = None):
        """
        Initialize the service with repository classes.

        Args:
            repositories: Optional list of repository classes that inherit
            from ShiftRepository. If None, will initialize with PostgresShiftRepository.

        Raises:
            ValueError: If PostgresShiftRepository initialization fails.
        """
        super().__init__()

        if repositories is None:
            repositories = [PostgresShiftRepository]

        self._initialize_repositories(repositories)
        self._validate_postgres_repository()

    def _initialize_repositories(
        self, repositories: List[Type[ShiftRepository]]
    ) -> None:
        """
        Initialize repository instances
        from the provided repository classes.

        Args:
            repositories: List of repository
            classes that inherit from CRUDShiftRepository.

        Raises:
            ValueError: If a repository doesn't
            inherit from CRUDShiftRepository.
        """
        initialized_repos = []

        for repo_class in repositories:
            if not issubclass(repo_class, ShiftRepository):
                raise ValueError(
                    f"Repository {repo_class.__name__}"
                    "must inherit from ShiftRepository"
                )

            repo_instance = repo_class()
            initialized_repos.append(repo_instance)

            if isinstance(repo_instance, CRUDShiftRepository):
                self.crud_shift_repository = repo_instance

        self.shift_repositories = initialized_repos

    def _validate_postgres_repository(self) -> None:
        """
        Ensure that exactly one PostgresShiftRepository
        instance is available.

        Raises:
            ValueError: If PostgresShiftRepository
            is missing or if multiple instances found.
        """
        postgres_repos = [
            repo
            for repo in self.shift_repositories
            if isinstance(repo, PostgresShiftRepository)
        ]

        if not postgres_repos:
            raise ValueError("PostgresShiftRepository is required but not found")
        if len(postgres_repos) > 1:
            raise ValueError("Multiple PostgresShiftRepository instances found")

        self.crud_shift_repository = postgres_repos[0]

    def _prepare_entity_with_metadata(
        self, entity: Dict[Any, Any], model: ShiftComment | ShiftAnnotation
    ) -> ShiftComment | ShiftAnnotation:
        """
        Prepare a shift data object with metadata.

        Args:
            shift_data (Dict[Any, Any]): Raw shift comment or annotation data from
            the database.

        Returns:
            ShiftComment: A ShiftComment object with metadata included.
            ShiftAnnotation: A ShiftAnnotation object with metadata included.
        """
        shift_data_load = model.model_validate(entity)
        metadata_dict = get_latest_metadata(entity)
        shift_data_load.metadata = Metadata.model_validate(metadata_dict)

        return shift_data_load

    class Config:
        arbitrary_types_allowed = True
