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
module: theforeman_subnet
version_added: "2.4"
author: Steven Bambling(@smbambling)
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
    theforeman_generate_locations_dict, theforeman_generate_domains_dict, \
    theforeman_generate_organizations_dict, theforeman_compare_query_values, \
    theforeman_obtain_resource_id # NOQA


def create(
           module, name, description, network_type, network, mask, gateway,
           dns_primary, dns_secondary, ipam, ip_from, ip_to, vlanid,
           boot_mode, dhcp_proxy, dns_proxy, tftp_proxy, domains,
           locations, organizations, url
          ):

    # Create list of domain dictionaries
    set_domains = theforeman_generate_domains_dict(module, url, domains)

    # Create list of locations dictionaries
    set_locations = theforeman_generate_locations_dict(module, url, locations)

    # Create list of organizations dictionaries
    set_organizations = theforeman_generate_organizations_dict(module, url,
                                                            organizations)

    # Get resource ID for Foreman DHCP,DNS,TFTP proxies
    if dhcp_proxy or dns_proxy or tftp_proxy:
        myurl = url + "/api/smart_proxies"
        data = {}
        method = 'GET'
        search_parameter = 'name'
    if dhcp_proxy:
        search_value = dhcp_proxy
        dhcp_proxy_id = theforeman_obtain_resource_id(module, myurl, data, method,
                                                   search_parameter,
                                                   search_value)
    else:
        dhcp_proxy_id = None

    if dns_proxy:
        search_value = dns_proxy
        dns_proxy_id = theforeman_obtain_resource_id(module, myurl, data, method,
                                                  search_parameter,
                                                  search_value)
    else:
        dns_proxy_id = None

    if tftp_proxy:
        search_value = tftp_proxy
        tftp_proxy_id = theforeman_obtain_resource_id(module, myurl, data, method,
                                                   search_parameter,
                                                   search_value)
    else:
        tftp_proxy_id = None

    # Query Foreman API for current Domains
    myurl = url + "/api/subnets"
    data = {
        'subnet': {
          "name": name,
          "description": description,
          "network_type": network_type,
          "network": network,
          "mask": mask,
          "gateway": gateway,
          "dns_primary": dns_primary,
          "dns_secondary": dns_secondary,
          "ipam": ipam,
          "from": ip_from,
          "to": ip_to,
          "vlanid": vlanid,
          "boot_mode": boot_mode,
          "dhcp_id": dhcp_proxy_id,
          "dns_id": dns_proxy_id,
          "tftp_id": tftp_proxy_id,
          "domains": set_domains,
          "locations": set_locations,
        }
    }
    method = 'GET'
    search_parameter = 'name'
    search_value = name

    # Obtain Foreman resource ID
    resource_id = theforeman_obtain_resource_id(module, myurl, data, method,
                                             search_parameter, search_value)

    # Create subnet if it does not exist
    if resource_id == 'None' or resource_id == '':
        if not module.check_mode:
            myurl = url + "/api/subnets"
            method = 'POST'
            (query_out, info) = theforeman_query(module, myurl, data, method)
            return False, query_out, True
        else:
            return False, "Subnet %s will be created" % (name), True
    else:
        # Obtain current Foreman resouce values
        myurl = url + "/api/subnets/%s" % (resource_id)
        (query_out, info) = theforeman_query(module, myurl, data, method)

        # Update domain if set/return values differ
        (diff_val, diff_data) = theforeman_compare_query_values(module, url, data,
                                                             query_out,
                                                             set_domains,
                                                             set_locations,
                                                             set_organizations)
        if diff_val != 0:
            method = 'PUT'
            (query_out, info) = theforeman_query(module, myurl, diff_data, method)
            return False, query_out, True

        return False, query_out, False


def remove(module, name, description, locations, url):
    return 'blah'


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            description=dict(type='str', default=''),
            network_type=dict(type='str', required=True,
                              choices=['IPv4', 'IPv6']),
            network=dict(type='str', required=True),
            mask=dict(type='str', required=True),
            gateway=dict(type='str', required=False, default=''),
            dns_primary=dict(type='str', required=False, default=''),
            dns_secondary=dict(type='str', required=False, default=''),
            ipam=dict(type='str', required=False,
                      choices=['DHCP', 'Internal DB', 'None'],
                      default='DHCP'),
            ip_from=dict(type='str', required=False, default=''),
            ip_to=dict(type='str', required=False, default=''),
            vlanid=dict(type='str', required=False, default=''),
            boot_mode=dict(type='str', required=False,
                           choices=['DHCP', 'Static'], default='DHCP'),
            dhcp_proxy=dict(type='str', required=False, default=None),
            dns_proxy=dict(type='str', required=False, default=None),
            tftp_proxy=dict(type='str', required=False, default=None),
            domains=dict(type='list', required=False, default=[]),
            locations=dict(type='list', required=False, default=[]),
            organizations=dict(type='list', required=False, default=[]),
            url=dict(required=False, default='https://127.0.01:443'),
            url_username=dict(type='str', default='admin'),
            url_password=dict(type='str', no_log=True, required=True),
            state=dict(default='present', choices=['present', 'absent']),
        ),
        supports_check_mode=True
    )

    name = module.params['name']
    description = module.params['description']
    network_type = module.params['network_type']
    network = module.params['network']
    mask = module.params['mask']
    gateway = module.params['gateway']
    dns_primary = module.params['dns_primary']
    dns_secondary = module.params['dns_secondary']
    ipam = module.params['ipam']
    ip_from = module.params['ip_from']
    ip_to = module.params['ip_to']
    vlanid = module.params['vlanid']
    boot_mode = module.params['boot_mode']
    dhcp_proxy = module.params['dhcp_proxy']
    dns_proxy = module.params['dns_proxy']
    tftp_proxy = module.params['tftp_proxy']
    domains = module.params['domains']
    locations = module.params['locations']
    organizations = module.params['organizations']
    url = module.params['url']
    module.params['force_basic_auth'] = True
    # url_username and url_password on auto passed into fetch_url
    module.params['url_username']
    module.params['url_password']
    state = module.params['state']

    if state == 'present':
        (rc, query_out, changed) = create(
            module, name, description, network_type, network, mask, gateway,
            dns_primary, dns_secondary, ipam, ip_from, ip_to, vlanid,
            boot_mode, dhcp_proxy, dns_proxy, tftp_proxy, domains, locations,
            organizations, url
        )

    if state == 'absent':
        (rc, query_out, changed) = remove(
            module, name, description, network_type, network, mask, gateway,
            dns_primary, dns_secondary, ipam, ip_from, ip_to, vlanid,
            boot_mode, dhcp_proxy, dns_proxy, tftp_proxy, domains, locations,
            organizations, url
        )

    if rc != 0:
        module.fail_json(msg="failed", result=query_out)
    module.exit_json(msg="success", result=query_out, changed=changed)


if __name__ == '__main__':
    main()
