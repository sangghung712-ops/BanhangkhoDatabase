from db import get_connection

conn=get_connection()
print("thanh cong" ,conn.is_connected())
conn.close()