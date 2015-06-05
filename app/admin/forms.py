from wtforms import (
    StringField, BooleanField, SelectField, TextAreaField,
    ValidationError, SubmitField
)

from flask.ext.wtf import Form
from wtforms.validators import Required, Length, Email, URL, Optional

from app.models import User, Role

from flask.ext.babel import gettext
_ = gettext


class EditProfileAdminForm(Form):
    email = StringField(_('Email'), validators=[Required(), Length(1, 64),
                                             Email()])
    username = StringField(_('Tên đăng nhập'), validators=[Required(), 
                                                                Length(1, 64)])
    confirmed = BooleanField(_('Đã xác nhận'))
    enabled = BooleanField(_('Đã kích hoạt'))
    role = SelectField(_('Chức danh'), coerce=int)
    name = StringField(_('Tên hiển thị'), validators=[Length(0, 64)])
    location = StringField(_('Vị trí'), validators=[Length(0, 64)])
    url = StringField('URL', validators=[Optional(), URL(), Length(0, 64)])
    submit = SubmitField(_('Lưu lại'))

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError(_('Email đã có người sử dụng'))

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError(_('Tên đăng nhập đã có người sử dụng'))

class EditNomForm(Form):
    id = StringField(_('ID'), validators=[Length(0, 16)])
    character= StringField(_('Chữ Nôm'), validators=[Length(1, 16)])
    keyword = StringField(_('Từ khóa'), validators=[Length(1, 16)])
    meaning = TextAreaField(_('Giải nghĩa'))
    submit = SubmitField(_('Lưu lại'))
