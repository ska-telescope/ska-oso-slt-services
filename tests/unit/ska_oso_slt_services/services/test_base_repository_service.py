import pytest

from ska_oso_slt_services.repository.postgres_shift_repository import (
    PostgresShiftRepository,
)
from ska_oso_slt_services.repository.shift_repository import CRUDShiftRepository
from ska_oso_slt_services.services.base_repository_service import BaseRepositoryService


class TestBaseRepositoryService:
    @pytest.fixture
    def mock_postgres_repository(self):
        class MockPostgresRepo(PostgresShiftRepository):
            pass

        return MockPostgresRepo

    @pytest.fixture
    def mock_eda_repository(self):
        class MockEDARepo(CRUDShiftRepository):
            def get_shifts(self, **kwargs):
                return []

            def get_shift(self, shift_id: str):
                return None

            def create_shift(self, shift):
                return shift

            def update_shift(self, shift_id, shift):
                return shift

            def delete_shift(self, shift_id: str):
                return True

        return MockEDARepo

    @pytest.fixture
    def base_repository_service(self, mock_postgres_repository, mock_eda_repository):
        repositories = [mock_postgres_repository, mock_eda_repository]
        return BaseRepositoryService(repositories=repositories)

    def test_initialize_repositories_success(self, base_repository_service):
        """Test successful initialization of repositories."""
        assert len(base_repository_service.shift_repositories) == 2
        assert all(
            isinstance(repo, CRUDShiftRepository)
            for repo in base_repository_service.shift_repositories
        )

    def test_validate_postgres_repository_success(self):
        """Test successful validation of postgres repository."""

        class MockPostgresRepo(PostgresShiftRepository):
            pass

        class MockEDARepo(CRUDShiftRepository):
            def get_shifts(self, **kwargs):
                return []

            def get_shift(self, shift_id: str):
                return None

            def create_shift(self, shift):
                return shift

            def update_shift(self, shift_id, shift):
                return shift

            def delete_shift(self, shift_id: str):
                return True

        service = BaseRepositoryService(repositories=[MockPostgresRepo, MockEDARepo])
        service._validate_postgres_repository()
        # Should not raise any exception

    def test_validate_postgres_repository_multiple(self):
        """Test validation when multiple postgres repositories are present."""

        class MockPostgresRepo1(PostgresShiftRepository):
            pass

        class MockPostgresRepo2(PostgresShiftRepository):
            pass

        with pytest.raises(ValueError) as exc_info:
            BaseRepositoryService(repositories=[MockPostgresRepo1, MockPostgresRepo2])
        assert "Multiple PostgresShiftRepository instances found" in str(exc_info.value)
