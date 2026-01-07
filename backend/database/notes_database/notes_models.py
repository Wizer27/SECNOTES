from sqlalchemy import Table,Column,MetaData,Integer,String


metadata_obj = MetaData()

notes_table = Table(
    "notes_table",
    metadata_obj,
    Column("username",String),
    Column("note",String),
    Column("password",String),
    Column("time_to_die",String),
    Column("id",String,primary_key=True)
)