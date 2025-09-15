from datetime import datetime
from typing import ClassVar, Optional
from shared.database import BaseModelDatabaseMixin
from shared.file_database.models import (
    File as FileModel,
    FileType,
    DownloadLink as DownloadLinkModel,
)


class File(BaseModelDatabaseMixin):
    model: ClassVar[type[FileModel]] = FileModel

    id: Optional[int] = None
    name: str
    uuid: Optional[str] = None
    file_type: FileType
    user_id: int
    original_file: Optional["File"] = None
    # presigned_url: Optional[str] = None


class DownloadLink(BaseModelDatabaseMixin):
    model: ClassVar[type[DownloadLinkModel]] = DownloadLinkModel

    id: Optional[int] = None    
    bucket_name: str
    presigned_url: str
    expires_at: datetime
    created_at: Optional[datetime] = None
    accessed_count: Optional[int] = None
    is_active: Optional[bool] = True
    file_id: int
    file: Optional[File] = None

