from flask import render_template, redirect, url_for, flash, current_app

from flask.ext.login import login_required, current_user

from app import db

from app.settings import settings
from app.settings.forms import (
    EditProfileForm, ChangePasswordForm, ChangeEmailForm,
    ContactForm
)

from app.email import send_email

from flask.ext.babel import gettext
_ = gettext


@settings.route('/')
@login_required
def index():
    return redirect(url_for('.edit_profile'))

class Tab():
    def __init__(self, number, text):
        self.number = number
        self.text = text

@settings.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit() and current_user.enabled:
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.url = form.url.data
        db.session.add(current_user)
        flash(_('Hồ sơ đã được cập nhật'))
        return redirect(url_for('.edit_profile'))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.url.data = current_user.url
    selection = Tab(1, _('Chỉnh sửa hồ sơ'))
    return render_template('settings/settings.html', 
                           form=form, selection=selection)


@settings.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit() and current_user.enabled:
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            flash(_('Mật khẩu của bạn đã được thay đổi'))
            return redirect(url_for('.change_password'))
        else:
            flash(_('Mật khẩu chưa đúng'))
    selection = Tab(3, _('Thay đổi mật khẩu'))
    return render_template("settings/settings.html",
                           form=form, selection=selection)


@settings.route('/change-email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit() and current_user.enabled:
        if current_user.verify_password(form.password.data):
            new_email = form.email.data
            token = current_user.generate_email_change_token(new_email)
            send_email(new_email, _('Xác nhận địa chỉ email mới'),
                       'auth/email/change_email',
                       user=current_user, token=token)
            flash(_('Một email với hướng dẫn xác nhận đã được gửi đi'))
            return redirect(url_for('.change_email_request'))
        else:
            flash(_('Mật khẩu chưa đúng'))
    selection = Tab(4, _('Thay đổi email'))
    return render_template("settings/settings.html",
                           form=form, selection=selection)


@settings.route('/change-email/<token>')
@login_required
def change_email(token):
    if current_user.change_email(token):
        flash(_('Xác nhận thành công địa chỉ email mới'))
    else:
        flash(_('Yêu cầu không hợp lệ'))
    return redirect(url_for('main.index'))


@settings.route('/contact', methods=['GET', 'POST'])
@login_required
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        send_email(current_app.config['MAIL_ADMIN'],
                   form.subject.data,
                   'admin/email/contact',
                   user=current_user,
                   body=form.body.data)
        flash(_('Gửi thư đi thành công, chúng tôi sẽ liên hệ lại với bạn'))
        form.subject.data = ""
        form.body.data = ""
    selection = Tab(5, _('Liên hệ'))
    return render_template("settings/settings.html",
                           form=form, selection=selection)
