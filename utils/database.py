from sqlalchemy import create_engine, Column, String, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Torrent(Base):
    __tablename__ = "torrents"

    hash = Column(String(40), primary_key=True)
    file_name = Column(Text, nullable=False)
    category = Column(String(50))
    announce_url = Column(Text)
    timestamp = Column(String(50))  # Storing as ISO string to match existing data
    submitted_by = Column(String(50))
    block_number = Column(Integer)
    exact_source = Column(Text)  # URL to the .torrent file or source page

    def to_dict(self):
        return {
            "hash": self.hash,
            "file_name": self.file_name,
            "category": self.category,
            "announce_url": self.announce_url,
            "timestamp": self.timestamp,
            "submitted_by": self.submitted_by,
            "block_number": self.block_number,
            "exact_source": self.exact_source,
        }


class Setting(Base):
    __tablename__ = "settings"

    id = Column(String(50), primary_key=True)
    key = Column(String(50), primary_key=True)
    value = Column(Text)


# Simple helper for database initialization
def get_db_engine(db_path="magnetbank.db"):
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    return engine


def get_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()
