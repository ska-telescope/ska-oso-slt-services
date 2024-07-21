from ska_db_oda.unit_of_work.postgresunitofwork import create_connection_pool


connection_pool = create_connection_pool()
print("Connected")