from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, NumberAttribute, \
    UTCDateTimeAttribute, UnicodeSetAttribute, NumberSetAttribute, \
    BooleanAttribute

"""
This module contains the DynamoDB tables class that specifies the tables 
in the database used to store user posts and comments.
"""

class UserFile(Model):
    """
    This class inferits from the Model object of pynamodb with the
    structure of the DynamoDB table UserFile.
    Used to store the file post that users uploaded.

    Each record will have an unique id (sort key), author_id (hash key),
    author, timestamp, and filenames.
    """

    class Meta:
        table_name = 'UserFile'
        # Specifies the region
        region = 'us-east-1'
        # Optional: Specify the hostname only if it needs to be changed from the default AWS setting
        # host = 'http://localhost'
        # Specifies the write capacity
        write_capacity_units = 400
        # Specifies the read capacity
        read_capacity_units = 400

    id = UnicodeAttribute(range_key=True)
    author_id = NumberAttribute(hash_key=True)
    author = UnicodeAttribute()
    timestamp = UTCDateTimeAttribute()
    s3_filename = UnicodeAttribute()
    original_filename = UnicodeAttribute()


class Comment(Model):
    """
    This class inferits from the Model object of pynamodb with the
    structure of the DynamoDB table Comment.
    Used to store the comments that users post.

    Each record will have an body, timestamp (sort key), author_id,
    author, and image_id (hash key).
    """
    class Meta:
        table_name = "Comment"
        # Specifies the region
        region = 'us-east-1'
        # Optional: Specify the hostname only if it needs to be changed from the default AWS setting
        # host = 'http://localhost'
        # Specifies the write capacity
        write_capacity_units = 400
        # Specifies the read capacity
        read_capacity_units = 400

    body = UnicodeAttribute()
    # body_html = UnicodeAttribute()
    timestamp = UTCDateTimeAttribute(range_key=True)
    author_id = NumberAttribute()
    author = UnicodeAttribute()
    image_id = UnicodeAttribute(hash_key=True)

    # @staticmethod
    # def on_changed_body(target, value, oldvalue, initiator):
    #     allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
    #                     'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
    #                     'h1', 'h2', 'h3', 'p']
    #     target.body_html = bleach.linkify(bleach.clean(
    #         markdown(value, output_format='html'),
    #         tags=allowed_tags, strip=True))


class UserImage(Model):
    """
    This class inferits from the Model object of pynamodb with the
    structure of the DynamoDB table UserImage.
    Used to store the photo post that users uploaded.

    Each record will have an unique id (sort key), title, author_id (hash key),
    timestamp, and three filenames.
    """

    class Meta:
        table_name = 'UserImage'
        # Specifies the region
        region = 'us-east-1'
        # Optional: Specify the hostname only if it needs to be changed from the default AWS setting
        # host = 'http://localhost'
        # Specifies the write capacity
        write_capacity_units = 400
        # Specifies the read capacity
        read_capacity_units = 400

    id = UnicodeAttribute(range_key=True)
    title = UnicodeAttribute()
    author_id = NumberAttribute(hash_key=True)
    timestamp = UTCDateTimeAttribute()
    base_filename = UnicodeAttribute()
    original_filename = UnicodeAttribute()
    thumbnail_filename = UnicodeAttribute()


def delete_all():
    """Delete all records in three DynamoDB tables.
    """
    if UserFile.exists():
        UserFile.delete_table()
    if UserImage.exists():
        UserImage.delete_table()
    if Comment.exists():
        Comment.delete_table()


def create_all():
    """Create three DynamoDB tables.
    """
    if not UserFile.exists():
        UserFile.create_table()

    if not UserImage.exists():
        UserImage.create_table()

    if not Comment.exists():
        Comment.create_table()
