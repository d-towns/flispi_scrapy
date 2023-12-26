from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
import sys
from pathlib import Path

parent_dir = Path(__file__).resolve().parent.parent

# Add the 'flispi_scrapy' directory to sys.path
sys.path.append(str(parent_dir))

# Now you can import the PropertyEntity from sql.property
from models.sql.property import PropertyEntity

# SQLite setup (assuming your SQLite DB is named 'local.db')

# connection_string = "sqlite:///landbank_properties.sqlite"
# engine = create_engine(connection_string, echo=True)
# Session = sessionmaker(bind=engine)
# session = Session(bind=engine)

sqlite_engine = create_engine("sqlite:///landbank_properties.sqlite")
SQLiteSession = sessionmaker(bind=sqlite_engine)
sqlite_session = SQLiteSession()

# PostgreSQL setup
# Replace these with your actual credentials
postgresql_db_url = "postgresql://postgres:EGdG4aGDA-3C33FfCF*a34cB3AFfDB6G@monorail.proxy.rlwy.net:15871/railway"
postgresql_engine = create_engine(postgresql_db_url)
PostgreSQLSession = sessionmaker(bind=postgresql_engine)
postgresql_session = PostgreSQLSession()

# Assuming the table name is 'your_table_name'
table_name = 'properties'
metadata = MetaData()
table = Table(table_name, metadata) 


# Fetch all data from the SQLite table
sqlite_data = sqlite_session.query(PropertyEntity).all()

# Insert data into PostgreSQL table
for row in sqlite_data:
    insert_stmt = table.insert().values(**row.__dict__)
    print(insert_stmt)
    postgresql_session.execute('INSERT INTO properties (id, address, city, state, zip_code, county, latitude, longitude, property_type')

# Commit and close sessions
postgresql_session.commit()
sqlite_session.close()
postgresql_session.close()
