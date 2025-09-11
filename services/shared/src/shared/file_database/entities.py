

from typing import ClassVar, Optional
from shared.database import BaseModelDatabaseMixin
from shared.file_database.models import File as FileModel, FileType


class File(BaseModelDatabaseMixin):
    model: ClassVar[type[FileModel]] = FileModel

    id: Optional[int] = None
    name: str
    uuid: Optional[str] = None
    file_type: FileType
    user_id: int
    original_file_id: Optional[int] = None
    # original_file: Optional["File"] = None
    # converted_file: Optional["File"] = None

