import uuid
from fastapi import HTTPException, status, UploadFile
import cloudinary.uploader
import logging
logger = logging.getLogger(__name__)
class LogoUpload:

    @staticmethod
    def _save_image(image: UploadFile) -> dict:
        """
        Upload image to Cloudinary and return dict:
        {
            "url": "...",
            "public_id": "logos/logo_xxx"
        }
        """
        allow_types = ["image/png", "image/jpeg", "image/jpg"]

        if image.content_type not in allow_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file type. Only PNG, JPG, and JPEG are allowed."
            )

        ext = image.filename.split(".")[-1]
        unique_name = f"logo_{uuid.uuid4()}.{ext}"

        try:
            upload_result = cloudinary.uploader.upload(
                image.file,
                public_id=f"logos/{unique_name}",  # full path
                overwrite=True
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload image: {str(e)}"
            )

        return {
            "url": upload_result["secure_url"],
            "public_id": upload_result["public_id"]
        }

    @staticmethod
    def _delete_logo(public_id: str):
        """
        Delete image from Cloudinary using its public_id:
        e.g. logos/logo_123.png
        """
        if not public_id:
            logger.warning("No public_id passed → skip deleting")
            return False

        try:
            result = cloudinary.uploader.destroy(public_id)
            logger.info(f"Cloudinary delete result: {result}")

            # Cloudinary returns:
            # { "result": "ok" } → image deleted
            # { "result": "not found" } → wrong public_id
            return result.get("result") == "ok"

        except Exception as e:
            logger.error(f"Cloudinary deletion error: {str(e)}")
            return False
