from flask import (
    render_template, redirect, request, url_for, flash, abort,
    current_app
)
from flask.ext.login import (
    login_user, logout_user, login_required,
    current_user
)
from app import db, cache
from app.models import User
from app.email import send_email
from app.auth import auth
from app.auth.forms import LoginForm, RegistrationForm, \
    PasswordResetRequestForm, PasswordResetForm

from flask.ext.babel import gettext
_ = gettext


@auth.before_app_request
def before_request():
    if current_user.is_authenticated():
        current_user.ping()
        if not current_user.confirmed \
                and request.endpoint[:5] != 'auth.' \
                and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous() or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated():
        return abort(404)
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            cache.clear()
            return redirect(request.args.get('next') or url_for('main.index'))
        flash(_('Mật khẩu và email không khớp'))
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    cache.clear()
    flash(_('Bạn đã đăng xuất thành công'))
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email, 'Xác nhận tài khoản của bạn',
                   'auth/email/confirm', user=user, token=token)
        flash(_('Một thư xác nhận đã được gửi tới địa chỉ email đăng ký'))
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash(_('Bạn đã xác nhận địa chỉ email thành công!'))
        send_email(current_app.config['MAIL_ADMIN'],
                   'Có thành viên mới xác nhận',
                   'admin/email/new_user', user=current_user)
    else:
        flash(_('Đường dẫn xác nhận không đúng hoặc đã hết hạn'))
    return redirect(url_for('main.index'))


@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Xác nhận tài khoản của bạn',
               'auth/email/confirm', user=current_user, token=token)
    flash(_('Một thư xác nhận MỚI đã được gửi tới địa chỉ email bạn đăng ký'))
    return redirect(url_for('main.index'))


@auth.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    if not current_user.is_anonymous():
        return redirect(url_for('main.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()
            send_email(user.email, 'Khôi phục mật khẩu',
                       'auth/email/reset_password',
                       user=user, token=token,
                       next=request.args.get('next'))
        flash(_('Một thư hướng dẫn khôi phục mật khẩu đã được gửi đi'))
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if not current_user.is_anonymous():
        return redirect(url_for('main.index'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            return redirect(url_for('main.index'))
        if user.reset_password(token, form.password.data):
            flash(_('Mật khẩu của bạn đã được thay đổi'))
            return redirect(url_for('auth.login'))
        else:
            return redirect(url_for('main.index'))
    return render_template('auth/reset_password.html', form=form)
