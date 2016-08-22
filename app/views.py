"""Views for Interact application, which currently includes

- Landing : with three options for unauthenticated users (1) download zip or
            (2) authenticate and commence copying
- Progress : page containing live updates on server's progress, redirects to
             new content once pull or clone is complete
"""

from app.auth import HubAuth
from flask import current_app
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from operator import xor
from threading import Thread
from webargs import fields
from webargs.flaskparser import use_args

from . import util
from .download_file_and_redirect import download_file_and_redirect
from .pull_from_github import pull_from_github

index_args = {
    'file': fields.Str(),

    'repo': fields.Str(),
    'path': fields.List(fields.Str()),
}


@current_app.route(current_app.config['URL'])
@use_args(index_args)
def landing(args):
    """Landing page containing option to download OR (exclusive) authenticate.

    Option 1
    --------

        ?file=public_file_url

    Example: ?file=http://localhost:8000/README.md

    Authenticates, then downloads file into user's system.

    Option 2
    --------

        ?repo=data8_github_repo_name&path=file_or_folder_name&path=other_folder

    Example: ?repo=textbook&path=notebooks&path=chapter1%2Fintroduction.md

    Authenticates, then pulls content into user's file system.
    Note: Only the gh-pages branch is pulled from Github.
    """
    is_file_request = ('file' in args)
    is_git_request = ('repo' in args and 'path' in args)
    valid_request = xor(is_file_request, is_git_request)
    if not valid_request:
        return render_template('404.html')

    hubauth = HubAuth()

    # authenticate() returns either a username as a string or a redirect
    redirection = username = hubauth.authenticate()
    is_authenticated = isinstance(username, str)
    if not is_authenticated:
        values = []
        for k, v in args.items():
            if not isinstance(v, str):
                v = '&path='.join(v)
            values.append('%s=%s' % (k, v))
        return render_template(
            'landing.html',
            authenticate_link=redirection.location,
            download_links=util.generate_git_download_link(args),
            query='&'.join(values))

    # Start the user's server if necessary
    if not hubauth.notebook_server_exists(username):
        return redirect('/hub/home')

    if not current_app.tracker[username]:
        thread = Thread(
            target=execute_request,
            args=(current_app,
                  current_app.app_context(),
                  request.url,
                  username,
                  is_file_request,
                  args),
        )
        current_app.tracker[username] = thread
        util.emit_estimate_update(current_app.tracker)
    else:
        thread = None
    return render_template(
        'progress.html',
        username=username,
        reusing_thread=thread is None)


def execute_request(app, context, url, username, is_file_request, args):
    """Execute the request -- either a file load or a git pull.

    This process is ideally run on a separate thread, as all methods in here
    emit broadcasts to user-specific namespaces. In this case, the namespaces
    are uniquely identified by the user's `username`.
    """
    with context:
        try:
            if is_file_request:
                redirection = download_file_and_redirect(
                    username=username,
                    file_url=args['file'],
                    config=current_app.config,
                )
            else:
                redirection = pull_from_github(
                    username=username,
                    repo_name=args['repo'],
                    paths=args['path'],
                    config=current_app.config,
                )

            util.emit_redirect('/' + username, redirection)
            app.tracker.pop(username)
            util.emit_estimate_update(current_app.tracker)
            return redirection
        except BaseException as e:
            app.tracker[username].url = url
            app.tracker[username].error = e
            util.emit_redirect(username, url_for('error', username=username))


@current_app.route('/start/<string:username>')
def start(username):
    """Hack - GIL prevents Python from multi-threading.

    Instead, the landing view above returns the loading page immediately. The
    client then triggers this endpoint, which starts the thread
    """
    if current_app.tracker[username] is None:
        util.logger.info(
            'No thread for user: {}'.format(username))
    if current_app.tracker[username].is_alive():
        util.logger.info(
            'Thread already in progress for user: {}'.format(username))
    if not current_app.config['SUPPRESS_START']:
        util.logger.info(
            'Starting thread for user: {}'.format(username))
        current_app.tracker[username].start()
    return 'Done'


@current_app.route('/error/<string:username>')
def error(username):
    """Displays error information"""
    rv = render_template(
        'error.html',
        link_retry=current_app.tracker[username].url,
        log=current_app.tracker[username].error)
    current_app.tracker.pop(username)
    return rv


@current_app.route('/done')
def done():
    """Page containing information about completed process."""
    return render_template('done.html')
