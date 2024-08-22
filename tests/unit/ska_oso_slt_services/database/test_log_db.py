from unittest.mock import MagicMock, patch

from elasticsearch import Elasticsearch

from ska_oso_slt_services.data_access.logdb_data_access import LOGDBConnection


class TestLOGDBConnection:
    @patch.object(LOGDBConnection, "_create_connection")
    def test_singleton_instance(self, mock_create_connection):
        mock_es_client = MagicMock(spec=Elasticsearch)
        mock_create_connection.return_value = mock_es_client

        instance1 = LOGDBConnection()
        instance2 = LOGDBConnection()

        assert instance1 is instance2
        mock_create_connection.assert_called_once()
