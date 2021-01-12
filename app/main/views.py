from datetime import datetime
from flask import render_template, redirect, url_for, request, abort, \
    current_app, flash, make_response
from flask_login import current_user
from . import main
from .forms import PostForm, PostFormFile, EditProfileForm, CommentForm, FilterForm
from .. import db, uploaded_files, photos, aws_worker_session
from ..models import User
from ..dymodels import Comment, UserImage, UserFile
from .pipeline import process_files, process_profile_photo, \
    process_files_general
# from ..decorators import admin_required, permission_required
# from ..models import Permission
from flask_login import login_required
from ..utils.utils import paginate

"""
This module defines the routers of the main parts in Filestagram.
"""

"""Router to the homepage that shows all the files"""
@main.route("/", methods=["GET", "POST"])
def index():
    page = request.args.get('page', 1, type=int)
    show_followed = False
    show_yours = False

    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))
        show_yours = bool(request.cookies.get('show_yours', ''))

    if show_followed:
        followed_ids = [i.followed_id for i in current_user.followed]
        query = []
        for id in followed_ids:
            query.extend(UserImage.query(id, limit=5))

    elif show_yours:
        query = [i for i in UserImage.query(current_user.id)]
    else:
        query = [i for i in UserImage.scan()]

    # sort query by timestamp
    sort_key = lambda x: x.timestamp
    query.sort(key=sort_key, reverse=True)

    pagination = paginate(query, page,
                          per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
                          error_out=False)
    for file in pagination.items:
        file.original_url = aws_worker_session.get_object_presigned_url(
            '1779a3file', file.original_filename)

        file.thumbnail_url = aws_worker_session.get_object_presigned_url(
            '1779a3file', file.thumbnail_filename)

    return render_template('index.html', userfiles=pagination.items,
                           show_followed=show_followed, pagination=pagination,
                           show_yours=show_yours)


# @main.route("/files", methods=["GET", "POST"])
# # # @login_required
# # # def files():
# # #     # form = FilterForm()
# # #     # query = None
# # #     # if form.validate_on_submit():
# # #     #     query = form.query.data
# # #     # page = request.args.get('page', 1, type=int)
# # #     # if query:
# # #     #     files = [i for i in UserFile.query(current_user.id, UserFile.original_filename.contains(query))]
# # #     # else:
# # #     #     files = [i for i in UserFile.query(current_user.id)]
# # #     #
# # #     # # sort query by timestamp
# # #     # sort_key = lambda x: x.timestamp
# # #     # files.sort(key=sort_key, reverse=True)
# # #     #
# # #     # pagination = paginate(files, page,
# # #     #                       per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
# # #     #                       error_out=False)
# # #     # for file in pagination.items:
# # #     #     file.link = aws_worker_session.get_object_download_url('1779a3file',
# # #     #                                                            file.s3_filename,
# # #     #                                                            file.original_filename)
# # #     return redirect(url_for("main.files_filter", query = ""))
"""Router to the list of all files"""
@main.route("/files", methods=["GET", "POST"])
@main.route("/files/", methods=["GET", "POST"])
@main.route("/files/<query>", methods=["GET", "POST"])
@login_required
def files(query=""):
    form = FilterForm()
    query = query
    page = request.args.get('page', 1, type=int)
    if form.validate_on_submit():
        query = form.query.data
        page = 1


    if query:
        files = [i for i in UserFile.query(current_user.id, UserFile.original_filename.contains(query))]
    else:
        files = [i for i in UserFile.query(current_user.id)]

    # sort query by timestamp
    sort_key = lambda x: x.timestamp
    files.sort(key=sort_key, reverse=True)

    pagination = paginate(files, page,
                          per_page=current_app.config['FLASKY_FILE_PER_PAGE'],
                          error_out=False)
    for file in pagination.items:
        file.link = aws_worker_session.get_object_download_url('1779a3file',
                                                               file.s3_filename,
                                                               file.original_filename)

    return render_template("files.html", files=pagination.items, pagination=pagination, form = form, query = query)



@main.route("/file/<file_id>", methods=["GET"])
@login_required
def file(file_id):
    page = request.args.get('page', 1, type=int)

    file = [i for i in UserFile.query(current_user.id, UserFile.id == str(file_id) )][0]

    # sort query by timestamp
    file.link = aws_worker_session.get_object_download_url('1779a3file',
                                                               file.s3_filename,
                                                               file.original_filename)

    return render_template("file.html", file = file)


"""Router to the user profile page"""
@main.route("/user/<username>", methods=["GET", "POST"])
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    page = request.args.get("page", 1, type=int)

    images_post = [i for i in UserImage.query(user.id)]

    pagination = paginate(images_post, page,
                          per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
                          error_out=False)

    for file in images_post:
        file.original_url = aws_worker_session.get_object_presigned_url(
            '1779a3file', file.original_filename)
        file.thumbnail_url = aws_worker_session.get_object_presigned_url(
            '1779a3file', file.thumbnail_filename)


    return render_template("user.html", user=user, pagination=pagination,
                           userfiles=pagination.items)


"""Router to profile editing page"""
@main.route("/editProfile", methods=["GET", "POST"])
@login_required
def edit_user():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data

        if form.photo.data:
            base_name = form.data['photo'].filename
            data = form.photo.data
            if process_profile_photo(form, data, base_name):
                flash('Profile Photo Uploaded Succeed', 'success')
            else:
                flash('Internal Server Error', 'error')

        db.session.add(current_user)
        return redirect(url_for("main.user", username=current_user.username))
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template("editProfile.html", form=form,
                           image_url=current_user.image_url)


"""Router to the page that shows the details of a post with download link"""
@main.route("/post/<int:author_id>/<int:image_id>", methods=['GET', 'POST'])
@login_required
def post(author_id, image_id):
    show_more = False
    image = \
        [i for i in UserImage.query(author_id, UserImage.id == str(image_id))][
            0]

    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,
                          author_id=current_user.id,
                          author=current_user.username,
                          timestamp=datetime.now(),
                          image_id=str(image_id))
        comment.save()

        return redirect(
            url_for('main.post', image_id=image_id, author_id=author_id))

    page = request.args.get('page', 1, type=int)

    comments = [i for i in Comment.query(str(image_id))]

    pagination = paginate(comments, page,
                          per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
                          error_out=False)

    for comment in comments:
        comment.image_url = User.query.get(int(comment.author_id)).image_url

    user = User.query.get(int(image.author_id))

    image.image_url = user.image_url
    image.username = user.username
    image.original_url = aws_worker_session.get_object_presigned_url(
        '1779a3file', image.original_filename)
    image.thumbnail_url = aws_worker_session.get_object_presigned_url(
        '1779a3file', image.thumbnail_filename)

    return render_template("post.html", form=form, posts=[image],
                           comments=comments, pagination=pagination,
                           show_more=show_more)


"""Router to the image uploading page"""
@main.route("/upload_image", methods=['GET', 'POST'])
@login_required
def upload_image():
    form = PostForm()
    if form.validate_on_submit():
        current_user.follow(current_user)
        base_name = form.data['file'].filename
        data = form.file.data
        if process_files(form, data, base_name):
            flash('File Uploaded Succeed', 'success')
        else:
            flash('Internal Server Error', 'error')

        db.session.commit()
        return redirect(url_for('.index'))

    return render_template('upload.html', form=form)


"""Router to the file uploading page"""
@main.route("/upload_file", methods=['GET', 'POST'])
def upload_file():
    # upload a general file.
    form = PostFormFile()

    data = None
    alert = False
    if form.validate_on_submit():
        base_name = form.data['file'].filename
        data = form.file.data

        url = process_files_general(form, data, base_name)
        if url:
            flash('File Uploaded Succeed', 'success')
            data = {}
            data['link'] = url
            data['name'] = base_name

        else:
            flash('Internal Server Error', 'error')

        db.session.commit()

        if current_user.is_anonymous:
            alert = True

    return render_template('uploadFile.html', form=form, data=data, alert=alert)


"""Router to follow a specific user"""
@main.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('main.index'))
    if current_user.is_following(user):
        flash('You are already following this user.')
        return redirect(url_for('main.user', username=username))
    current_user.follow(user)
    return redirect(url_for('main.user', username=username))


"""Router to unfollow a specific user"""
@main.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    if not current_user.is_following(user):
        flash('You are not following this user.')
        return redirect(url_for('.user', username=username))
    current_user.unfollow(user)
    return redirect(url_for('.user', username=username))


"""Router to a a page that shows an user's followers"""
@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followers of",
                           endpoint='.followers', pagination=pagination,
                           follows=follows)


"""Router to a a page that shows all users that followed by the user"""
@main.route('/followed-by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followed by",
                           endpoint='.followed_by', pagination=pagination,
                           follows=follows)


"""Set the cookie for all posts"""
@main.route('/all')
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30 * 24 * 60 * 60)
    resp.set_cookie('show_yours', '', max_age=30 * 24 * 60 * 60)

    return resp


"""Set the cookie for the current user's posts"""
@main.route('/yours')
@login_required
def show_yours():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_yours', '1', max_age=30 * 24 * 60 * 60)
    resp.set_cookie('show_followed', '', max_age=30 * 24 * 60 * 60)
    return resp


"""Set the cookie for the posts of the current user's following accounts"""
@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30 * 24 * 60 * 60)
    resp.set_cookie('show_yours', '', max_age=30 * 24 * 60 * 60)
    return resp
