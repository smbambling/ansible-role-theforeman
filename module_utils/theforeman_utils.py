# This code is part of Ansible, but is an independent component.

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
            domain_id = theforeman_obtain_resource_id(module, myurl, data,
                                                      method,
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
            organization_id = theforeman_obtain_resource_id(module, myurl,
                                                            data, method,
                                                            search_parameter,
                                                            search_value)
            organization_dict = {"id": organization_id}
            set_organizations.append(organization_dict.copy())

    return set_organizations


# Generate list of operatingsystem IDs
def theforeman_gen_os_ids(module, url, operatingsystems):
    set_operatingsystems = []
    myurl = url + "/api/operatingsystems"
    data = {}
    method = 'GET'
    search_parameter = 'description'

    if operatingsystems:
        for i in operatingsystems:
            search_value = i
            operatingsystem_id = theforeman_obtain_resource_id(module, myurl,
                                                               data, method,
                                                               search_parameter, # NOQA
                                                               search_value)
            operatingsystem_dict = {"id": operatingsystem_id}
            set_operatingsystems.append(operatingsystem_dict.copy())

    return set_operatingsystems


# Parse input to generate list of resource IDs
def theforeman_parse_resource_id(resources):
    resource_ids = []

    if resources:
        for i in resources:
            resource_ids.append(i['id'])

    return resource_ids


# Compare current values against provided values
def theforeman_compare_values(module, url, query_data, query_out,
                              domains=[], locations=[],
                              organizations=[], operatingsystems=[]):

    # Set update trigger variable
    diff_val = 0

    for i in query_data.keys():
        if domains:
            set_domains = theforeman_parse_resource_id(domains)
            assigned_domains = theforeman_parse_resource_id(query_out['domains']) # NOQA
        else:
            set_domains = []
            if 'domain' in query_data[i].keys():
                assigned_domains = theforeman_parse_resource_id(query_out['domains']) # NOQA
                query_data.update({"domains": [{"id": ""}]})
            else:
                assigned_domains = []

        if locations:
            set_locations = theforeman_parse_resource_id(locations)
            assigned_locations = theforeman_parse_resource_id(query_out['locations']) # NOQA
        else:
            set_locations = []
            if 'locations' in query_data[i].keys():
                assigned_locations = theforeman_parse_resource_id(query_out['locations']) # NOQA
                query_data.update({"locations": [{"id": ""}]})
            else:
                assigned_locations = []

        if operatingsystems:
            set_operatingsystems = theforeman_parse_resource_id(operatingsystems) # NOQA
            assigned_operatingsystems = theforeman_parse_resource_id(query_out['operatingsystems']) # NOQA
        else:
            set_operatingsystems = []
            if 'operatingsystems' in query_data[i].keys():
                assigned_operatingsystems = theforeman_parse_resource_id(query_out['operatingsystems']) # NOQA
                query_data.update({"operatingsystems": [{"id": ""}]})
            else:
                assigned_operatingsystems = []

        for key, val in query_data[i].iteritems():
            if key == 'domains':
                if set(set_domains) != set(assigned_domains):
                    diff_val = diff_val + 1
            elif key == 'locations':
                if set(set_locations) != set(assigned_locations):
                    diff_val = diff_val + 1
            elif key == 'operatingsystems':
                if set(set_operatingsystems) != set(assigned_operatingsystems):
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
