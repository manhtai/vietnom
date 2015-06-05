from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, SubmitField
from wtforms.validators import Length

from flask.ext.pagedown.fields import PageDownField

from flask.ext.babel import gettext
_ = gettext


class PostForm(Form):
    keyword = StringField(_('Từ khóa'), validators=[Length(0, 16)])
    story = PageDownField(_('Mẩu chuyện'), validators=[Length(0, 320)])
    shared = BooleanField(_('Chia sẻ mẩu chuyện này'))
    submit = SubmitField(_('Lưu lại'))
