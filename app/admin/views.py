from app import db
from app.models import Role, User, Nom
from app.decorators import admin_required

from app.settings.views import Tab

from app.admin import admin
from app.admin.forms import EditProfileAdminForm, EditNomForm

from flask import (
    render_template, redirect, url_for, flash,
    Response, stream_with_context
)

from flask.ext.login import login_required

from flask.ext.babel import gettext
_ = gettext

@admin.route('/')
@login_required
@admin_required
def admin_index():
    return redirect(url_for('.add_nom'))


@admin.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.enabled = form.enabled.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.url = form.url.data
        db.session.add(user)
        flash(_('Hồ sơ đã được cập nhật'))
        return redirect(url_for('.edit_profile', id=user.id))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.enabled.data = user.enabled
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.url.data = user.url
    selection = Tab(1, _('Sửa hồ sơ của [%(name)s]', name=user.username))
    return render_template('admin/admin.html',
                           form=form, user=user, selection=selection)


@admin.route('/edit-nom/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_nom(id):
    nom = Nom.query.get_or_404(id)
    form = EditNomForm()
    if form.validate_on_submit():
        nom.id = form.id.data
        nom.character = form.character.data
        nom.keyword = form.keyword.data
        nom.meaning = form.meaning.data

        db.session.add(nom)

        return redirect(url_for('main.nom_view', id=nom.id))

    form.id.data = nom.id
    form.character.data = nom.character
    form.keyword.data = nom.keyword
    form.meaning.data = nom.meaning

    selection = Tab(3, _('Sửa chữ Nôm thứ %(nid)s', nid=nom.id))
    return render_template('admin/admin.html',
                           nom=nom, form=form, selection=selection)


@admin.route('/add-nom', methods=['GET', 'POST'])
@login_required
@admin_required
def add_nom():
    form = EditNomForm()
    if form.validate_on_submit():
        character = form.character.data
        nom = Nom.query.filter_by(character=character).first()
        if nom is None:
            nom = Nom(character=form.character.data,
                    keyword=form.keyword.data,
                    meaning = form.meaning.data)
            db.session.add(nom)

        return redirect(url_for('.edit_nom', id=nom.id))

    selection = Tab(0, _('Thêm chữ Nôm'))
    return render_template('admin/admin.html',
                           form=form, selection=selection)


@admin.route('/export/search.js')
@login_required
@admin_required
def export_search():
    def generate():
        yield """
            var docs = 
            [
            """
        for nom in Nom.query.all():
            json = str(nom.to_json()) + ","
            yield json
        end = """
            ];

            // init lunr
            var idx = lunr(function () {
            this.field('k', 10);
            });
            // add each document to be index
            for(var index in docs) {
            idx.add(docs[index]);
            }
            """ 
        yield end
    return Response(stream_with_context(generate()),
                    mimetype='text/javascript')

