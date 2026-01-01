from sqlalchemy import String,Integer,MetaData,Table,Column


metadata_obj = MetaData()

table = Table(
    "secnotes_log",
    metadata_obj,
    Column("username",String,primary_key=True),
    Column("hash_psw",String)
)

