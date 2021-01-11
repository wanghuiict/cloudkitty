import flask
import voluptuous
from cloudkitty.api.v2 import base
from cloudkitty import validation_utils
from cloudkitty.api.v2 import utils as api_utils
from werkzeug import exceptions as http_exceptions
from cloudkitty.common import policy

class Example(base.BaseResource):
   afruit = ['banana', 'strawberry', 'grape']
   anfruit = ['orange', 'apple']

   @api_utils.add_input_schema('query', {
        voluptuous.Optional('fruit'): api_utils.SingleQueryParam(str),
   })
   @api_utils.add_output_schema({
       voluptuous.Required(
           'message',
           default='This is an example endpoint',
       ): validation_utils.get_string_type(),
   })
   def get(self, fruit=None):
       policy.authorize(flask.request.context, 'example:get_example', {})
       return {}

   @api_utils.add_input_schema('body', {
       voluptuous.Required('fruit'): validation_utils.get_string_type(),
   })
   def post(self, fruit=None):
       policy.authorize(flask.request.context, 'example:submit_fruit', {})
       if not fruit:
           raise http_exceptions.BadRequest(
               'You must submit a fruit',
           )
       if fruit not in Example.afruit and fruit not in Example.anfruit:
           raise http_exceptions.Forbidden(
               'You submitted a forbidden fruit',
           )
       return {
           'message': 'Your fruit is %s %s.' %('an' if fruit in Example.anfruit else 'a', fruit),
       }
