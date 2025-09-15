from datetime import datetime
import enum
from uuid import uuid4
from sqlalchemy import VARCHAR, ForeignKey, func
from sqlalchemy.orm import Mapped, relationship, mapped_column, selectinload
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
    # presigned_url: Mapped[str] = mapped_column(nullable=True)

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

    download_links: Mapped[list["DownloadLink"]] = relationship(back_populates="file")

    @staticmethod
    def get_select_in_load():
        return [selectinload(File.converted_file), selectinload(File.original_file)]


class DownloadLink(Base):
    __tablename__ = "download_links"
    
    bucket_name: Mapped[str] = mapped_column(VARCHAR(100), nullable=False)
    presigned_url: Mapped[str] = mapped_column(nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    accessed_count: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationship
    file_id: Mapped[int] = mapped_column(ForeignKey("files.id"), nullable=False)
    file: Mapped[File] = relationship(back_populates="download_links")

    @staticmethod
    def get_select_in_load():
        return [selectinload(DownloadLink.file)]
    
    def is_expired(self):
        return datetime.now() > self.expires_at

    def is_valid(self):
        return self.is_active and not self.is_expired()
