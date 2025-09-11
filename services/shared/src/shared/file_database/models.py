import enum
from uuid import uuid4
from sqlalchemy import VARCHAR, ForeignKey
from sqlalchemy.orm import Mapped, relationship, mapped_column
from shared.database import Base


class FileType(enum.StrEnum):
    VIDEO = "video"
    AUDIO = "audio"


class File(Base):
    __tablename__ = "files"
    id: Mapped[int] = mapped_column("id", autoincrement=True, primary_key=True)
    name: Mapped[str] = mapped_column(VARCHAR(255), unique=True)
    uuid: Mapped[str] = mapped_column(default=lambda: str(uuid4()), unique=True)
    file_type: Mapped[str] = mapped_column(VARCHAR(50), nullable=False)  # video, audio
    user_id: Mapped[int] = mapped_column(nullable=False)

    # Relationships
    original_file_id: Mapped[int] = mapped_column(ForeignKey("files.id"), nullable=True)
    # 'original_file' is the parent of this file (e.g., the video for the mp3)
    original_file: Mapped["File"] = relationship(
        remote_side=[id],
        back_populates="converted_file",
    )

    # 'converted_file' is a one-to-one relationship
    converted_file: Mapped["File"] = relationship(
        back_populates="original_file", single_parent=True
    )
