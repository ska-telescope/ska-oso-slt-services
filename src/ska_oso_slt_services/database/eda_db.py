import pyhdbpp


class EDADB:
    def __init__(self, config) -> None:
        self.config = config
        self.api_class = "pyhdbpp.timescaledb.timescaledb.TimescaleDbReader"
        self.cluster_name = (
            "databaseds-tango-base.ci-ska-skampi-hm-213 mid.svc.cluster.local"
        )
        self.telescope = "ska_mid"
        self.url_1 = f"tango://{self.cluster_name}:{self.config.DB_CLUSTER_PORT}"
        self.device_trl = f"{self.url_1}/{self.telescope}/tm_subarray_node/1/obsstate"

    def create_reader(self):
        config_part = f"{self.config.DB_USER}:{self.config.DB_PASSWORD}"
        config_part_2 = f"{self.config.DB_PORT}/{self.config.database}"
        return pyhdbpp.reader(
            apiclass=self.api_class,
            config=f"{config_part}@{self.config.DB_HOST}:{config_part_2}",
        )
