import logging
from botocore.exceptions import ClientError
import boto3
from datetime import datetime


class AWS_session:
    def __init__(self, profile_name):
        self.woker_session = boto3.Session( aws_access_key_id="dummy",
                                            aws_secret_access_key="dummy",)
        self.s3_client = self.woker_session.client('s3')
        self.s3_resource = self.woker_session.resource('s3')
        self.cloudwatch_client = self.woker_session.client('cloudwatch')

    def upload_file_to_s3(self, file_name, bucket, object_name=None, ACL=None):
        """Upload a file to an S3 bucket

         :param file_name: File to upload
         :param bucket: Bucket to upload to
         :param object_name: S3 object name. If not specified then file_name is used
         :param ACL: Set Access Control List
         :return: True if file was uploaded, else False
         """

        # If S3 object_name was not specified, use file_name
        if object_name is None:
            object_name = file_name

        # Upload the file
        try:
            self.s3_client.upload_file(file_name, bucket, object_name)

            if ACL:
                self.s3_resource.ObjectAcl(bucket, object_name).put(ACL=ACL)

        except ClientError as e:
            logging.error(e)
            return False
        return True

    def get_object_presigned_url(self, bucket_name, file_name):
        """Get the presigned URL of a file in an S3 bucket

         :param bucket_name: the name of the S3 bucket
         :param file_name: the file name
         :return: the presigned URL
         """
        url = self.s3_client.generate_presigned_url('get_object', Params={'Bucket': bucket_name,
                                                                          'Key': file_name},
                                                    ExpiresIn=100)
        return url

    def get_object_download_url(self, bucket_name, object_name, original_name):
        """Get the URL of a file in an S3 bucket for downloading

         :param bucket_name: the name of the S3 bucket
         :param object_name: the object name
         :param original_name: the original file name
         :return: the download URL
         """
        url = self.s3_client.generate_presigned_url('get_object', Params={'Bucket': bucket_name,
                                                                          'Key': object_name,
                                                                          "ResponseContentDisposition": f"attachment; filename={original_name}",
                                                                          },

                                                    ExpiresIn=3600)

        return url

    def get_object_url(self, bucket_name, file_name):
        """Get the object URL of a file in an S3 bucket

         :param bucket_name: the name of the S3 bucket
         :param file_name: the file name
         :return: the URL
         """
        return f'https://{bucket_name}.s3.amazonaws.com/{file_name}'
