from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from wtforms import ValidationError

from app.models import User
from flask.ext.babel import gettext
_ = gettext


class LoginForm(Form):
    email = StringField(_('Email'), 
                        validators=[
                            Required(message=_('Thông tin bắt buộc')),
                            Email(_('Địa chỉ email không hợp lệ'))
    ])
    password = PasswordField(_('Mật khẩu'), 
                             validators=[
                                 Required(message=_('Không được để trống'))
                             ])
    remember_me = BooleanField(_('Giữ tôi đăng nhập'))
    submit = SubmitField(_('Đăng nhập'))


class RegistrationForm(Form):
    email = StringField(_('Email'), validators=[Required(), Length(1, 64),
                                           Email()])
    username = StringField(_('Tên đăng nhập'), validators=[
        Required(), Length(4, 16, message=_('Độ dài chỉ từ 4 đến 16 kí tự.')), 
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, 
               _('Tên đăng nhập chỉ được phép có chữ cái, '
                 'chữ số, dấu chấm và gạch dưới'))])
    password = PasswordField(_('Mật khẩu'), validators=[
        Length(6, 32, message=_('Độ dài mật khẩu phải từ 6 đến 32 kí tự.')), 
        Required(), EqualTo('password2', message=_('Mật khẩu phải khớp.'))])
    password2 = PasswordField(_('Xác nhận mật khẩu'), validators=[Required()])
    submit = SubmitField(_('Đăng ký'))

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(_('Email đã có người sử dụng'))

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError(_('Tên đăng nhập đã có người sử dụng'))


class PasswordResetRequestForm(Form):
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                             Email()])
    submit = SubmitField(_('Khôi phục'))


class PasswordResetForm(Form):
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                             Email()])
    password = PasswordField(_('Mật khẩu mới'), validators=[
        Length(6, 32),
        Required(), EqualTo('password2', message=_('Mật khẩu phải khớp'))])
    password2 = PasswordField(_('Xác nhận mật khẩu'), validators=[Required()])
    submit = SubmitField('Đổi mật khẩu')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError(_('Địa chỉ email không đúng'))

