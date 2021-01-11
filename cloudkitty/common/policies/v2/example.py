from oslo_policy import policy

from cloudkitty.common.policies import base

example_policies = [
    policy.DocumentedRuleDefault(
        name='example:get_example',
        check_str=base.ROLE_ADMIN,
        description='Get an example message',
        operations=[{'path': '/v2/ihs/example',
                     'method': 'GET'}]),
    policy.DocumentedRuleDefault(
        name='example:submit_fruit',
        check_str=base.UNPROTECTED,
        description='Submit a fruit',
        operations=[{'path': '/v2/ihs/example',
                     'method': 'POST'}]),
]

def list_rules():
    return example_policies

