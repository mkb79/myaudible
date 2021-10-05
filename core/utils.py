import json
from typing import Dict, Optional, TYPE_CHECKING

from audible.aescipher import AESCipher

if TYPE_CHECKING:
    from django.core.files.uploadedfile import UploadedFile


def get_data_from_uploaded_auth_file(
        file: 'UploadedFile',
        password: Optional[str] = None
    ) -> Dict:

    data = file.read()
    try:
        data = json.loads(data)
    except UnicodeDecodeError:
        crypter = AESCipher(password=password)
        data = crypter.from_bytes(data)

    if 'ciphertext' in data:
        crypter = AESCipher(password=password)
        data = crypter.from_dict(data)

    data = json.loads(data)

    return data

