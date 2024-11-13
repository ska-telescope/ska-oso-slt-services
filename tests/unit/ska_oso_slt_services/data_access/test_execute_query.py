from unittest.mock import MagicMock, patch

import pytest
from psycopg2.errors import DatabaseError, DataError, InternalError

from ska_oso_slt_services.data_access.postgres.execute_query import (
    PostgresDataAccess,
    TableCreator,
)


class MockCursor:
    def __init__(self):
        self.execute = MagicMock()
        self.fetchone = MagicMock(return_value=(1,))
        self.fetchall = MagicMock(return_value=[(1, "test"), (2, "test2")])
        self.rowcount = 1

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


class MockConnection:
    def __init__(self):
        self.mock_cursor = MockCursor()
        self.commit = MagicMock()
        self.rollback = MagicMock()
        self.cursor = MagicMock(return_value=self.mock_cursor)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        return False


@pytest.fixture
def mock_connection():
    return MockConnection()


@pytest.fixture
def mock_postgres_connection(mock_connection):
    with patch(
        "ska_oso_slt_services.data_access.postgres.execute_query.PostgresConnection"
    ) as mock_pg:
        connection_factory = MagicMock()
        connection_factory.connection.return_value = mock_connection
        mock_pg.return_value.get_connection.return_value = connection_factory
        yield mock_pg.return_value


@pytest.fixture
def mock_table_creator():
    with patch(
        "ska_oso_slt_services.data_access.postgres.execute_query.get_table_creator"
    ) as mock:
        table_creator = MagicMock()
        table_creator.create_slt_table = MagicMock()
        mock.return_value = table_creator
        yield table_creator


@pytest.fixture
def postgres_data_access(mock_postgres_connection, mock_table_creator):
    return PostgresDataAccess()


class TestPostgresDataAccess:

    @pytest.mark.parametrize("error_class", [DatabaseError, InternalError, DataError])
    def test_insert_database_error(
        self, postgres_data_access, mock_connection, error_class
    ):
        # Arrange
        query = "INSERT INTO test_table (column1) VALUES (%s)"
        params = ("test_value",)

        # Setup cursor to raise error
        mock_connection.mock_cursor.execute.side_effect = error_class("Database error")

        # Act/Assert
        with pytest.raises(error_class):
            postgres_data_access.insert(query, params)

        # Assert rollback was called
        mock_connection.rollback.assert_called_once()

    def test_insert_success(
        self, postgres_data_access, mock_connection, mock_table_creator
    ):
        # Arrange
        query = "INSERT INTO test_table (column1) VALUES (%s)"
        params = ("test_value",)

        # Act
        result = postgres_data_access.insert(query, params)

        # Assert
        assert result == (1,)
        mock_connection.mock_cursor.execute.assert_called_once_with(query, params)
        mock_connection.mock_cursor.fetchone.assert_called_once()
        mock_connection.commit.assert_called_once()
        mock_table_creator.create_slt_table.assert_called_once()

    def test_update_success(self, postgres_data_access, mock_connection):
        # Arrange
        query = "UPDATE test_table SET column1 = %s"
        params = ("new_value",)

        # Act
        result = postgres_data_access.update(query, params)

        # Assert
        assert result == 1
        mock_connection.mock_cursor.execute.assert_called_once_with(query, params)
        mock_connection.commit.assert_called_once()

    def test_update_database_error(self, postgres_data_access, mock_connection):
        # Arrange
        query = "UPDATE test_table SET column1 = %s"
        params = ("test_value",)

        # Setup cursor to raise error
        mock_connection.mock_cursor.execute.side_effect = DatabaseError(
            "Database error"
        )

        # Act/Assert
        with pytest.raises(DatabaseError):
            postgres_data_access.update(query, params)

        # Assert rollback was called
        mock_connection.rollback.assert_called_once()

    def test_get_success(self, postgres_data_access, mock_connection):
        # Arrange
        query = "SELECT * FROM test_table"
        params = ()

        # Act
        result = postgres_data_access.get(query, params)

        # Assert
        assert result == [(1, "test"), (2, "test2")]
        mock_connection.mock_cursor.execute.assert_called_once_with(query, params)
        mock_connection.mock_cursor.fetchall.assert_called_once()

    def test_get_one_success(
        self, postgres_data_access, mock_connection, mock_table_creator
    ):
        # Arrange
        query = "SELECT * FROM test_table WHERE id = %s"
        params = (1,)

        # Act
        result = postgres_data_access.get_one(query, params)

        # Assert
        assert result == (1,)
        mock_connection.mock_cursor.execute.assert_called_once_with(query, params)
        mock_connection.mock_cursor.fetchone.assert_called_once()
        mock_table_creator.create_slt_table.assert_called_once()

    @pytest.mark.parametrize("error_class", [DatabaseError, InternalError, DataError])
    def test_get_database_error(
        self, postgres_data_access, mock_connection, error_class
    ):
        # Arrange
        query = "SELECT * FROM test_table"
        params = ()

        # Setup cursor to raise error
        mock_connection.mock_cursor.execute.side_effect = error_class("Database error")

        # Act/Assert
        with pytest.raises(error_class):
            postgres_data_access.get(query, params)

    def test_get_one_database_error(self, postgres_data_access, mock_connection):
        # Arrange
        query = "SELECT * FROM test_table WHERE id = %s"
        params = (1,)

        # Setup cursor to raise error
        mock_connection.mock_cursor.execute.side_effect = DatabaseError(
            "Database error"
        )

        # Act/Assert
        with pytest.raises(DatabaseError):
            postgres_data_access.get_one(query, params)

        # Assert rollback was called
        mock_connection.rollback.assert_called_once()


class TestTableCreator:
    @patch("ska_oso_slt_services.data_access.postgres.execute_query.PostgresConnection")
    def test_create_slt_table_sql_content(self, mock_postgres_connection):
        """Test the SQL content of the create table statement"""
        # Arrange
        # Create mock cursor
        mock_cursor = MagicMock()

        # Create mock connection factory
        mock_connection_factory = MagicMock()

        # Create mock connection
        mock_connection = MagicMock()

        # Setup the chain of returns
        mock_postgres_connection.return_value.get_connection.return_value = (
            mock_connection_factory
        )
        mock_connection_factory.connection.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        # Act
        table_creator = TableCreator()

        # Add debug print statements

        table_creator.create_slt_table()
