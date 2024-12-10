

from typing import List, Optional, Type
from pydantic import BaseModel, Field


from ska_oso_slt_services.repository.postgres_shift_repository import (
    CRUDShiftRepository,
    PostgresShiftRepository,
)


class BaseRepositoryService(BaseModel):
    """
    Base class for services that manage repositories with PostgreSQL requirement.
    """
    shift_repositories: List[CRUDShiftRepository] = Field(default_factory=list)
    postgres_repository: Optional[PostgresShiftRepository] = None

    def __init__(self, repositories: List[Type[CRUDShiftRepository]]):
        """
        Initialize the service with repository classes.

        Args:
            repositories: List of repository classes that inherit from CRUDShiftRepository.

        Raises:
            ValueError: If no repositories provided or if PostgresShiftRepository is missing.
        """
        super().__init__()
        if not repositories:
            raise ValueError("At least one repository must be provided")
        
        self._initialize_repositories(repositories)
        self._validate_postgres_repository()

    def _initialize_repositories(self, repositories: List[Type[CRUDShiftRepository]]) -> None:
        """
        Initialize repository instances from the provided repository classes.

        Args:
            repositories: List of repository classes that inherit from CRUDShiftRepository.

        Raises:
            ValueError: If a repository doesn't inherit from CRUDShiftRepository.
        """
        initialized_repos = []
        
        for repo_class in repositories:
            if not issubclass(repo_class, CRUDShiftRepository):
                raise ValueError(
                    f"Repository {repo_class.__name__} must inherit from CRUDShiftRepository"
                )
            
            repo_instance = repo_class()
            initialized_repos.append(repo_instance)
            
            if isinstance(repo_instance, PostgresShiftRepository):
                self.postgres_repository = repo_instance
        
        self.shift_repositories = initialized_repos

    def _validate_postgres_repository(self) -> None:
        """
        Ensure that exactly one PostgresShiftRepository instance is available.

        Raises:
            ValueError: If PostgresShiftRepository is missing or if multiple instances found.
        """
        postgres_repos = [
            repo for repo in self.shift_repositories 
            if isinstance(repo, PostgresShiftRepository)
        ]

        if not postgres_repos:
            raise ValueError("PostgresShiftRepository is required but not found")
        if len(postgres_repos) > 1:
            raise ValueError("Multiple PostgresShiftRepository instances found")

    class Config:
        arbitrary_types_allowed = True