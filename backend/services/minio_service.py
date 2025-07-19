from minio import Minio
from minio.error import S3Error
from flask import current_app

class MinioService:
    def __init__(self, app_config):
        self.client = Minio(
            app_config.MINIO_ENDPOINT,
            access_key=app_config.MINIO_ACCESS_KEY,
            secret_key=app_config.MINIO_SECRET_KEY,
            secure=False  # Nếu dùng HTTPS thì để True
        )
        self.bucket = app_config.MINIO_BUCKET_NAME
        # Tạo bucket nếu chưa có
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except Exception as e:
            print(f"Warning: Could not initialize MinIO bucket: {e}")
            # Bucket sẽ được tạo khi cần thiết

    def upload_file(self, file_obj, filename, content_type):
        try:
            # Đảm bảo bucket tồn tại
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
            
            self.client.put_object(
                self.bucket,
                filename,
                file_obj,
                length=-1,  # Đọc hết stream
                part_size=10*1024*1024,  # 10MB
                content_type=content_type
            )
            return True, f"File '{filename}' uploaded to bucket '{self.bucket}'"
        except S3Error as e:
            return False, str(e)
        except Exception as e:
            return False, f"MinIO error: {str(e)}"

    def delete_file(self, filename):
        try:
            self.client.remove_object(self.bucket, filename)
            return True, f"File '{filename}' deleted from bucket '{self.bucket}'"
        except S3Error as e:
            return False, str(e)

    def get_file(self, filename):
        try:
            return self.client.get_object(self.bucket, filename)
        except S3Error as e:
            return None

    def list_files(self):
        try:
            objects = self.client.list_objects(self.bucket)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            return [] 