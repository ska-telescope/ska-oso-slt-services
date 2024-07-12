import pyhdbpp


class EDADB:
    def __init__(self) -> None:
        self.host = "<timescaledb_host_name>"
        self.database = "<database name>"
        self.user = "<database user>"
        self.password = "<database password>"
        self.port = "<port>"
        self.api_class = "pyhdbpp.timescaledb.timescaledb.TimescaleDbReader"
        self.cluster_name = (
            "databaseds-tango-base.ci-ska-skampi-hm-213 mid.svc.cluster.local"
        )
        self.telescope = "ska_mid"
        self.cluster_port = 10000
        self.url_1 = f"tango://{self.cluster_name}:{self.cluster_port}"
        self.device_trl = f"{self.url_1}/{self.telescope}/tm_subarray_node/1/obsstate"

    def create_reader(self):
        return pyhdbpp.reader(
            apiclass=self.api_class,
            config=(
                f"{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
            ),
        )
