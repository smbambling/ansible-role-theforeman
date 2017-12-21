# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Steven Bambling <smbambling@gmail.com>, 2017-2018
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

try:
    import json
except ImportError:
    import simplejson as json

from ansible.module_utils.urls import fetch_url


# Submit query to Foreman API
def theforeman_query(module, url, data, method):
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    url = url + '?per_page=9999999999'

    response, info = fetch_url(
        module, url, method=method, headers=headers, data=json.dumps(data)
    )

    if (
        info['status'] != 201 and
        info['status'] != 200 and
        info['status'] != 404
       ):
        module.fail_json(
            msg="%s \n %s" % (info['msg'], info['body'])
        )

    try:
        json_out = json.loads(response.read())
    except:
        json_out = ''

    return json_out, info


# Obtain ID of Foreman resource based on specified parameter
def theforeman_obtain_resource_id(module, url, data, method,
                               search_parameter, search_value):
    (query_out, info) = theforeman_query(module, url, data, method)

    for i in query_out['results']:
        if search_value in i[search_parameter]:
            return i['id']

    # return nothing if ID can't be found
    return ''


# Generate list of domains dicts
def theforeman_generate_domains_dict(module, url, domains):
    set_domains = []
    myurl = url + "/api/domains"
    data = {}
    method = 'GET'
    search_parameter = 'name'

    if domains:
        for i in domains:
            search_value = i
            domain_id = theforeman_obtain_resource_id(module, myurl, data, method,
                                                   search_parameter,
                                                   search_value)
            domain_dict = {"id": domain_id}
            set_domains.append(domain_dict.copy())

    return set_domains


# Generate list of locations dicts
def theforeman_generate_locations_dict(module, url, locations):
    set_locations = []
    myurl = url + "/api/locations"
    data = {}
    method = 'GET'
    search_parameter = 'name'

    if locations:
        for i in locations:
            search_value = i
            location_id = theforeman_obtain_resource_id(module, myurl, data,
                                                     method,
                                                     search_parameter,
                                                     search_value)
            location_dict = {"id": location_id}
            set_locations.append(location_dict.copy())

    return set_locations


# Generate list of organizations dicts
def theforeman_generate_organizations_dict(module, url, organizations):
    set_organizations = []
    myurl = url + "/api/organizations"
    data = {}
    method = 'GET'
    search_parameter = 'name'

    if organizations:
        for i in organizations:
            search_value = i
            organization_id = theforeman_obtain_resource_id(module, myurl, data, method,
                                                         search_parameter,
                                                         search_value)
            organization_dict = {"id": organization_id}
            set_organizations.append(organization_dict.copy())

    return set_organizations


# Parse input to generate list of resource IDs
def theforeman_parse_resource_id(resources):
    resource_ids = []

    if resources:
        for i in resources:
            resource_ids.append(i['id'])

    return resource_ids


# Compare current values against provided values
def theforeman_compare_query_values(module, url, query_data, query_out,
                                 domains=[], locations=[], organizations=[]):

    # Set update trigger variable
    diff_val = 0

    for i in query_data.keys():
        if domains:
            set_domains = theforeman_parse_resource_id(domains)
            assigned_domains = theforeman_parse_resource_id(query_out['domains'])
        else:
            set_domains = []
            if i != 'domain':
                assigned_domains = theforeman_parse_resource_id(query_out['domains'])
                query_data.update({"domains": [{"id": ""}]})
            else:
                assigned_domains = []

        if locations:
            set_locations = theforeman_parse_resource_id(locations)
            assigned_locations = theforeman_parse_resource_id(query_out['locations'])
        else:
            set_locations = []
            if i != 'location':
                assigned_locations = theforeman_parse_resource_id(query_out['locations'])
                query_data.update({"locations": [{"id": ""}]})
            else:
                assigned_locations = []

        for key, val in query_data[i].iteritems():
            if key == 'domains':
                if set(set_domains) != set(assigned_domains):
                    diff_val = diff_val + 1
            elif key == 'locations':
                if set(set_locations) != set(assigned_locations):
                    diff_val = diff_val + 1
            else:
                if val != query_out[key]:
                    diff_val = diff_val + 1

    return diff_val, query_data


# Generate list of avilable location IDs
def theforeman_query_location_ids(module, url):
    url = url + '/api/locations'
    data = {}
    method = 'GET'

    json_out = theforeman_query(module, url, data, method)

    if json_out == 'None' or json_out == '':
        module.fail_json(
            msg="""
                No locations returned in query response from Foreman from %s
            """
        )

    location_ids = []
    for i in json_out['results']:
        location_ids.append(i['id'])

    return location_ids


# Calculate CIDR network prefix from networok mask
def theforeman_calculate_cidr(netmask):
    return sum([bin(int(x)).count('1') for x in netmask.split('.')])
