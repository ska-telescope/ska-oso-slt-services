from unittest.mock import MagicMock, patch

from pyhdbpp.timescaledb import TimescaleDbReader

from ska_oso_slt_services.data_access.eda_data_access import EDADBConnection


class TestEDADBConnection:
    @patch.object(EDADBConnection, "_create_connection")
    def test_singleton_instance(self, mock_create_connection):
        mock_reader = MagicMock(spec=TimescaleDbReader)
        mock_create_connection.return_value = mock_reader

        instance1 = EDADBConnection()
        instance2 = EDADBConnection()

        assert instance1 is instance2

        mock_create_connection.assert_called_once()
