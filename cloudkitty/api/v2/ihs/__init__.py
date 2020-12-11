from cloudkitty.api.v2 import utils as api_utils


def init(app):
    api_utils.do_init(app, 'ihs', [
        {
            'module': __name__ + '.' + 'example',
            'resource_class': 'Example',
            'url': 'example',
        },
    ])
    return app

