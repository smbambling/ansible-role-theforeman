#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Steven Bambling <smbambling@gmail.com>
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: theforeman_location
version_added: "2.4"
author: Steven Bambling(@smbambling)

There is a weird quirk, where this module will NOT clear all locations
but if a list is set it will make sure that those not in the list are removed
'''

EXAMPLES = '''
'''

RETURN = '''
'''

try:
    import json
except ImportError:
    import simplejson as json # NOQA

# Ignore PEP8 QA here as it does not conform Ansible requirements
from ansible.module_utils.basic import AnsibleModule # NOQA
from ansible.module_utils.urls import fetch_url # NOQA
from ansible.module_utils.theforeman_utils import theforeman_query, \
    theforeman_compare_values, theforeman_obtain_resource_id # NOQA


def create(module, name, description, url):

    # Query Foreman API for current Domains
    myurl = url + "/api/locations"
    data = {
        "location": {
          "name": name,
          "description": description,
        }
    }
    method = 'GET'
    search_parameter = 'name'
    search_value = name

    # Obtain Foreman resource ID
    resource_id = theforeman_obtain_resource_id(module, myurl, data, method,
                                                search_parameter, search_value)

    # Create location if it does not exist
    if resource_id == 'None' or resource_id == '':
        if not module.check_mode:
            myurl = url + "/api/locations"
            method = 'POST'
            (query_out, info) = theforeman_query(module, myurl, data, method)
            return False, query_out, True
        else:
            return False, "Domain %s will be created" % (name), True
    else:
        # Obtain current Foreman resource values
        myurl = url + "/api/locations/%s" % (resource_id)
        (query_out, info) = theforeman_query(module, myurl, data, method)

        # Update location if set/return values differ
        (diff_val, diff_data) = theforeman_compare_values(module, url, data,
                                                          query_out,
                                                          "", "", "", "")
        if diff_val != 0:
            myurl = url + "/api/locations/%s" % (query_out['id'])
            method = 'PUT'
            (query_out, info) = theforeman_query(module, myurl, diff_data, method)
            return False, query_out, True

        return False, query_out, False


def remove(module, name, description, url):
    # Query Foreman API for current Domains
    myurl = url + "/api/locations/%s" % (name)
    data = {
        "name": name,
    }
    method = 'GET'
    (query_out, info) = theforeman_query(module, myurl, data, method)
    if query_out == 'None' or query_out == '':
        return False, query_out, False
    else:
        if not module.check_mode:
            method = 'DELETE'
            (query_out, info) = theforeman_query(module, myurl, data, method)
            return False, query_out, True
        else:
            return False, "Domain %s will be removed" % (name), True


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            description=dict(type='str', default=""),
            url=dict(required=False, default='https://127.0.01:443'),
            url_username=dict(type='str', default='admin'),
            url_password=dict(type='str', no_log=True, required=True),
            state=dict(default='present', choices=['present', 'absent']),
        ),
        supports_check_mode=True
    )

    name = module.params['name']
    description = module.params['description']
    url = module.params['url']
    module.params['force_basic_auth'] = True
    module.params['url_username']
    module.params['url_password']

    # url_username and url_password on auto passed into fetch_url
    state = module.params['state']

    if state == 'present':
        (rc, query_out, changed) = create(
            module, name, description, url
        )

    if state == 'absent':
        (rc, query_out, changed) = remove(
            module, name, description, url
        )

    if rc != 0:
        module.fail_json(msg="failed", result=query_out)
    module.exit_json(msg="success", result=query_out, changed=changed)


if __name__ == '__main__':
    main()
