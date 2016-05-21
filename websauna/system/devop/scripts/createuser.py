"""ws-create-user script."""
import getpass

import os
import sys

from websauna.system.devop.cmdline import init_websauna
from websauna.system.user.events import UserCreated
from websauna.system.user.utils import get_user_class, get_user_registry

import transaction

from websauna.utils.time import now


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri> <email> [password]\n'
          '(example: "%s development.ini mikko@example.com")' % (cmd, cmd))
    sys.exit(1)


def create(request, username, email, password=None, source="command_line"):
    User = get_user_class(request.registry)
    dbsession = request.dbsession
    u = dbsession.query(User).filter_by(email=email).first()
    if u is not None:
        return u

    u = User(email=email, username=username)

    if password:
        user_registry = get_user_registry(request)
        user_registry.set_password(u, password)

    u.registration_source = source
    u.activated_at = now()
    dbsession.add(u)
    dbsession.flush()
    request.registry.notify(UserCreated(request, u))
    return u


def main(argv=sys.argv):

    if len(argv) < 3:
        usage(argv)

    config_uri = argv[1]
    request = init_websauna(config_uri)

    if len(argv) == 4:
        password = argv[3]
    else:
        password = getpass.getpass("Password:")
        password2 = getpass.getpass("Password (again):")

        if password != password2:
            sys.exit("Password did not match")

    with transaction.manager:
        u = create(request, email=argv[2], username=argv[2], password=password)
        print("Created user #{}: {}, admin: {}".format(u.id, u.email, u.is_admin()))


if __name__ == "__main__":
    main()
