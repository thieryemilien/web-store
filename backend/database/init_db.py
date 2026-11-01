from backend.database.connection import Base, engine
from backend.models import entities


#Permite crear la tabla automaticamente
def init_db():
    Base.metadata.create_all(bind=engine)
    print("Tablas creadas correctamente en MySQL")


if __name__ == "__main__":
    init_db()