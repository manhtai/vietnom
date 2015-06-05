from wtforms import (
    StringField, ValidationError, SubmitField,
    PasswordField, TextAreaField
)

from wtforms.validators import Required, Length, Email, EqualTo, URL, Optional

from flask.ext.wtf import Form

from app.models import User

from flask.ext.babel import gettext
_ = gettext


class EditProfileForm(Form):
    name = StringField(_('Tên hiển thị'), validators=[Length(0, 64)])
    location = StringField(_('Vị trí'), validators=[Length(0, 64)])
    url = StringField(_('URL'), validators=[Optional(), URL(), Length(0, 64)])
    submit = SubmitField(_('Lưu lại'))


class ChangePasswordForm(Form):
    old_password = PasswordField(_('Mật khẩu hiện tại'), validators=[Required()])
    password = PasswordField(_('Mật khẩu mới'), validators=[
        Length(6, 32, message=_('Mật khẩu phải từ 6 đến 32 ký tự')),
        Required(), EqualTo('password2', message=_('Chưa khớp mật khẩu'))])
    password2 = PasswordField(_('Xác nhận mật khẩu mới'), validators=[Required()])
    submit = SubmitField(_('Đổi mật khẩu'))


class ChangeEmailForm(Form):
    email = StringField(_('Email mới'), validators=[Required(), Length(1, 64),
                                                 Email()])
    password = PasswordField(_('Mật khẩu'), validators=[Required()])
    submit = SubmitField(_('Đổi email'))

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(_('Email này đã được sử dụng'))


class ContactForm(Form):
    subject = StringField(_('Chủ đề'), validators=[Required(), Length(1, 64)])
    body = TextAreaField(_('Nội dung'), validators=[Required()])
    submit = SubmitField(_('Gửi đi'))
