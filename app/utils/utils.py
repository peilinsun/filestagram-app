from flask_uploads import UploadSet, ALL, extension
import os
import posixpath
from flask import render_template, session, redirect, url_for, request, abort, current_app, flash, make_response
from math import ceil
# from werkzeug import secure_filename, FileStorage

def paginate(items, page, per_page, error_out=False):
    if page < 1:
        if error_out:
            abort(404)
        else:
            page = 1

    paged_items = items[(page - 1) * per_page:page * per_page]

    if not paged_items and page != 1 and error_out:
        abort(404)

    total = len(items)

    return Pagination(page,per_page, total, paged_items, items)


class Pagination(object):
    """Internal helper class returned by :meth:`BaseQuery.paginate`.  You
    can also construct it from any other SQLAlchemy query object if you are
    working with other libraries.  Additionally it is possible to pass `None`
    as query object in which case the :meth:`prev` and :meth:`next` will
    no longer work.
    """

    def __init__(self, page, per_page, total, items, all_items):
        #: the unlimited query object that was used to create this
        #: pagination object.

        #: the current page number (1 indexed)
        self.page = page
        #: the number of items to be displayed on a page.
        self.per_page = per_page
        #: the total number of items matching the query
        self.total = total
        #: the items for the current page
        self.items = items

        self.all_items = all_items

    @property
    def pages(self):
        """The total number of pages"""
        if self.per_page == 0:
            pages = 0
        else:
            pages = int(ceil(self.total / float(self.per_page)))
        return pages

    def prev(self, error_out=False):
        """Returns a :class:`Pagination` object for the previous page."""

        return paginate(self.all_items, self.page - 1, self.per_page, error_out)

    @property
    def prev_num(self):
        """Number of the previous page."""
        if not self.has_prev:
            return None
        return self.page - 1

    @property
    def has_prev(self):
        """True if a previous page exists"""
        return self.page > 1

    def next(self, error_out=False):
        """Returns a :class:`Pagination` object for the next page."""

        return paginate(self.all_items, self.page + 1, self.per_page, error_out)

    @property
    def has_next(self):
        """True if a next page exists."""
        return self.page < self.pages

    @property
    def next_num(self):
        """Number of the next page"""
        if not self.has_next:
            return None
        return self.page + 1

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        """Iterates over the page numbers in the pagination.  The four
        parameters control the thresholds how many numbers should be produced
        from the sides.  Skipped page numbers are represented as `None`.
        This is how you could render such a pagination in the templates:

        .. sourcecode:: html+jinja

            {% macro render_pagination(pagination, endpoint) %}
              <div class=pagination>
              {%- for page in pagination.iter_pages() %}
                {% if page %}
                  {% if page != pagination.page %}
                    <a href="{{ url_for(endpoint, page=page) }}">{{ page }}</a>
                  {% else %}
                    <strong>{{ page }}</strong>
                  {% endif %}
                {% else %}
                  <span class=ellipsis>…</span>
                {% endif %}
              {%- endfor %}
              </div>
            {% endmacro %}
        """
        last = 0
        for num in range(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and \
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num

class CustomizeUploadSet(UploadSet):
    """
    This module inherits from the UploadSet class from flask_uploads with 
    method of saving the file.
    """

    def __init__(self, name='files', extensions=ALL, default_dest=None):
        """Initialize with filenames, file extentions and the default destination for 
        saving the file
        """
        super(CustomizeUploadSet, self).__init__(name, extensions, default_dest)

    def save(self, storage, folder=None, name=None):
        """Saves the target file in the designated destination.
        Used in app/main/pipeline.py

        storage: the target file
        folder: the folder name under the default file path
        name: specified file name
        """
        self.config.destination = "/tmp"
        if folder is None and name is not None and "/" in name:
            folder, name = os.path.split(name)
        basename = name
        if folder:
            target_folder = os.path.join(self.config.destination, folder)
        else:
            target_folder = self.config.destination
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)
        if os.path.exists(os.path.join(target_folder, basename)):
            basename = self.resolve_conflict(target_folder, basename)

        target = os.path.join(target_folder, basename)
        storage.save(target)

        if folder:
            re = posixpath.join(folder, basename)
        else:
            re = basename

        return re
