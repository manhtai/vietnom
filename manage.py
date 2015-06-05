import os
from app import create_app, db
from app.models import User, Role, Permission, Post, Nom
from flask.ext.script import Manager, Shell
from flask.ext.migrate import Migrate, MigrateCommand

app = create_app(os.getenv('CONFIG_ENV') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)

def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role, Permission=Permission,
                Post=Post, Nom=Nom)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)

@manager.command
def profile(length=25, profile_dir=None):
    """Start the application under the code profiler."""
    from werkzeug.contrib.profiler import ProfilerMiddleware
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[length],
                                      profile_dir=profile_dir)
    app.run()

@manager.command
def deploy():
    """Run deployment tasks."""
    from flask.ext.migrate import upgrade
    from app.models import Role

    # migrate database to latest revision
    upgrade()

    # create user roles
    Role.insert_roles()

@manager.command
def fixdb():
    from app.ext.json_sql.from_json import init_db

    # import database from json
    init_db()

if __name__ == '__main__':
    manager.run()
