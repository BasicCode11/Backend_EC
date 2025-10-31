import os
import uuid
import os
from fastapi import HTTPException, status  , UploadFile
LOGO_UPLOAD_URL = "app/static/images/"

class LogoUpload:
    @staticmethod 
    def _save_image(image: UploadFile) -> str:
        allow_types = ["image/png", "image/jpeg", "image/jpg"]
        if image.content_type not in allow_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file type. Only PNG, JPG, and JPEG are allowed."
            )
        os.makedirs(LOGO_UPLOAD_URL, exist_ok=True)
        file_extension = os.path.splitext(image.filename)[1]
        unique_name = f"{uuid.uuid4()}{file_extension}"
        save_path = os.path.join(LOGO_UPLOAD_URL, unique_name)

        try:
            with open(save_path, "wb") as buffer:
                buffer.write(image.file.read())

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save image: {str(e)}"
            )
        
        return f"/static/images/{unique_name}"
    

    @staticmethod
    def _delete_logo(image_path: str):
        """Delete a logo file from disk if it exists."""
        if not image_path:
            return
        real_path = image_path.replace("/static", "app/static")
        if os.path.exists(real_path):
            try:
                os.remove(real_path)
            except Exception:
                pass