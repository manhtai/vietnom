from flask import (
    render_template, redirect, url_for, abort,
    flash, request, current_app,
    Response, stream_with_context
)
from flask.ext.login import login_required, current_user

from app import db, cache
from app.models import User, Permission, Post, Nom

from app.main import main
from app.decorators import teller_required
from app.main.forms import PostForm

from flask.ext.babel import gettext
_ = gettext


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/nom')
def nom_index():
    page = request.args.get('page', 1, type=int)
    pagination = Nom.query.order_by(Nom.id).paginate(
        page, per_page=current_app.config['NOMS_PER_PAGE'],
        error_out=False
    )
    noms = pagination.items
    return render_template('main/nom_index.html',
                           noms=noms, pagination=pagination)


@main.route('/nom/<int:id>')
@login_required
def nom_view(id):
    nom = Nom.query.get_or_404(id)
    my_post = Post.query.filter_by(nom=nom, author=\
                                   current_user._get_current_object()).first()
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.filter_by(nom=nom, shared=True).\
        order_by(Post.id).\
        paginate(
            page, per_page=current_app.config['POST_PER_PAGE'],
            error_out=False
        )
    posts = pagination.items
    return render_template('main/nom_view.html',
                           nom=nom, my_post=my_post,
                           posts=posts, pagination=pagination)


@main.route('/nom/<int:id>/edit', defaults={'ver': ''}, methods=['GET', 'POST'])
@main.route('/nom/<int:id>/edit/<int:ver>', methods=['GET', 'POST'])
@login_required
@teller_required
def edit_post(id, ver):
    if ver and ver > 1:
        abort(404)
    nom = Nom.query.get_or_404(id)
    author = current_user._get_current_object()
    post = Post.query.filter_by(nom=nom, author=author).first()
    if post is None:
        post = Post(keyword=nom.keyword, story="", nom=nom, author=author)
        db.session.add(post)

    form = PostForm()
    if form.validate_on_submit():
        if post.keyword != form.keyword.data or \
                post.story != form.story.data:
            post.keyword_backup = post.keyword
            post.keyword = form.keyword.data
            post.story_backup = post.story
            post.story = form.story.data 
            post.shared = form.shared.data
            db.session.add(post)
        elif post.shared != form.shared.data:
            post.shared = form.shared.data
            db.session.add(post)
        cache.delete_memoized(user)
        return redirect(url_for('.nom_view', id=nom.id))

    form.keyword.data = post.keyword_backup if ver else post.keyword
    form.story.data = post.story_backup if ver else post.story
    form.shared.data = post.shared

    return render_template('main/nom_edit.html',
                           nom=nom, form=form, ver=ver)


@main.route('/nom/vote/<int:id>/<vote>')
@login_required
def vote_post(id, vote):
    post = Post.query.get_or_404(id)
    if vote == 'up':
        current_user.up(post)
    elif vote == 'down':
        current_user.down(post)
    return redirect(url_for('.nom_view', id=post.nom_id))


@main.route('/nom/copy/<int:id>')
@login_required
def copy_post(id):
    from_post = Post.query.get_or_404(id)
    user = current_user._get_current_object()
    to_post = Post.query.filter_by(author=user,
                                   nom_id=from_post.nom_id).first()
    if current_user.can(Permission.TELL):
        if to_post is None:
            to_post = Post(keyword=from_post.keyword,
                           story=from_post.story,
                           nom=from_post.nom,
                           author=user)
        else:
            to_post.keyword_backup = to_post.keyword
            to_post.keyword = from_post.keyword

            to_post.story_backup = to_post.story
            to_post.story = from_post.story

        db.session.add(to_post)
        return redirect(url_for('.edit_post', id=from_post.nom_id))
    else:
        flash(_('Xin lỗi, bạn không đủ quyền để sao chép câu chuyện'))
        return redirect(url_for('.nom_view', id=from_post.nom_id))


@main.route('/export/vietnom.csv')
@login_required
def export_csv():
    def generate():
        user=current_user._get_current_object()
        for post in user.posts.all():
            nom = Nom.query.get_or_404(post.nom_id)
            csv = '"{}","{}","{}","{}"\n'.format(post.nom_id, nom.character,
                                         post.keyword, post.story)
            yield csv
    return Response(stream_with_context(generate()), mimetype='text/csv')


@main.route('/user/<username>')
@login_required
@cache.memoize(60*5)
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.filter_by(author=user,shared=True).\
        order_by(Post.nom_id).\
        paginate(
            page, per_page=current_app.config['POST_PER_PAGE'],
            error_out=False,
        )
    posts = pagination.items
    return render_template('main/user.html', user=user,
                           posts=posts, pagination=pagination)

