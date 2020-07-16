#!/usr/bin/python3

import argparse
import logging
import os
import webbrowser

import requests
from requests.auth import HTTPBasicAuth
from terminaltables import AsciiTable

logging.basicConfig(
    format='%(asctime)s %(message)s',
    datefmt='%d/%m/%Y %H:%M:%S',
    level=logging.INFO
)
PARSER = argparse.ArgumentParser()

PARSER.add_argument(
    '--rancher-url',
    help='Rancher server url',
    type=str,
    required=True
)
PARSER.add_argument(
    '--rancher-access-key',
    help='Rancher API access key',
    type=str,
    required=True
)
PARSER.add_argument(
    '--rancher-secret-key',
    help='Rancher API secret key',
    type=str,
    required=True
)
PARSER.add_argument(
    '--docker-username',
    help='Your DockerHub username (mandatory if you have private private registries)',
    type=str,
    required=False
)
PARSER.add_argument(
    '--docker-password',
    help='Your DockerHub password (mandatory if you have private private registries)',
    type=str,
    required=False
)
PARSER.add_argument(
    '--quiet',
    '-q',
    help='Don\'t show result tab in console',
    type=bool,
    required=False,
    choices=[True, False],
    default=False
)
PARSER.add_argument(
    '--report',
    help='Generate report as HTML file. Example --report=my-report.html',
    type=str,
    required=False,
)
ARGS = PARSER.parse_args()

DOCKER_REGISTRY_API_URL = 'https://registry.hub.docker.com/v2'
DOCKER_REGISTRY_TAGS_LIST_ENDPOINT = '/repositories/{}/tags/'
DOCKER_HUB_URL = 'https://hub.docker.com'

DOCKER_HUB_USERNAME = ARGS.docker_username
DOCKER_HUB_PASSWORD = ARGS.docker_password

RANCHER_SERVER_URL = ARGS.rancher_url
RANCHER_API_URL = RANCHER_SERVER_URL + '/v2-beta'
RANCHER_API_STACKS_LIST_ENDPOINTS = '/stacks'
RANCHER_API_SERVICES_LIST_PER_STACK = RANCHER_API_STACKS_LIST_ENDPOINTS + '/{}/services'

UNWANTED_REGISTRY = ['registry.gitlab.com', 'quaio.io']

REPORT_FILE_NAME_TEMPLATE = 'report.template'
REPORT_FILE_NAME = ARGS.report


def get_tags_list(image_name):
    """
    :param image_name: repository or official image
    :return: array of available tags
    """
    tags = []
    r = get_request(DOCKER_REGISTRY_API_URL + DOCKER_REGISTRY_TAGS_LIST_ENDPOINT.format(image_name))
    if 'results' not in r:
        return tags
    for tag in r['results']:
        tags.append(tag['name'])
    return tags


def get_rancher_services_list():
    """
    :return: array of all system services
    """
    service_list = []
    stacks = get_request(
        RANCHER_API_URL + RANCHER_API_STACKS_LIST_ENDPOINTS + '?system=false',
        True
    )

    for stack in stacks['data']:
        services = get_request(
            RANCHER_API_URL + RANCHER_API_SERVICES_LIST_PER_STACK.format(stack['id']),
            True
        )

        stack_detail = {'name': stack['name'], 'services': []}
        for service in services['data']:
            image = (service['data']['fields']['launchConfig']['imageUuid']).replace('docker:', '')
            dots = image.find(':')

            if dots != -1:
                tag = image[dots + 1:len(image)]
                image = image[0: dots]
            else:
                tag = 'latest'

            # Officials image
            if image.find('/') == -1:
                image = 'library/' + image

            stack_detail['services'].append({
                'name': service['name'],
                'image': image,
                'tag': tag,
                'new_tag': False
            })
        service_list.append(stack_detail)
    return service_list


def get_last_tag(image_name):
    """
    :param image_name: repository or official image
    :return: last tag. Return 'latest' if it is the only one
    """
    url = DOCKER_REGISTRY_API_URL + DOCKER_REGISTRY_TAGS_LIST_ENDPOINT.format(image_name)
    # Main request
    r = get_request(url)
    if 'results' not in r:
        global DOCKER_HUB_USERNAME
        global DOCKER_HUB_PASSWORD
        # If no result, try to authenticate
        if not DOCKER_HUB_PASSWORD or not DOCKER_HUB_USERNAME:
            # Ask for credentials if not set on cli
            ask = input(
                'Image {} unknown\nDo you want to try with your DockerHub credentials ? (y/n) '.format(image_name))
            if ask in ['y', 'Y', 'yes']:
                DOCKER_HUB_USERNAME = input('Username ? ')
                DOCKER_HUB_PASSWORD = input('Password ? ')
            else:
                return 'undefined (Private repository ?)'

        r = get_request(url, jwt_auth=True, token=get_docker_token())
    if 'results' not in r:
        logging.error('Invalid password or username, by pass')
        return 'undefined'

    # on each case, return the last tag
    for tag in r['results']:
        if tag['name'] != 'latest':
            return tag['name']
    return 'latest'


def is_it_the_latest_tag():
    stacks = get_rancher_services_list()
    services_count = 0
    logging.info('{} stacks found for this environment'.format(len(stacks)))
    for stack in stacks:
        for service in stack['services']:
            services_count += 1
            if valid_registry(service['image']):
                actual_tag = service['tag']
                latest_tag = get_last_tag(service['image'])
                if actual_tag != latest_tag:
                    service['new_tag'] = latest_tag
    logging.info('{} services found for this environment'.format(services_count))
    return stacks


def valid_registry(image_name):
    """
    Check if image does not part of UNWANTED_REGISTRY
    :param image_name:
    :return: valid or not
    """
    for valid in UNWANTED_REGISTRY:
        if image_name.find(valid) != -1:
            logging.info('{} image ignored because not DockerHub registry'.format(image_name))
            return False
    return True


def get_request(url, basic_auth=False, jwt_auth=False, token=''):
    """
    Send a GET request
    :param token: Bearer token
    :param jwt_auth: if its need a Bearer token
    :param basic_auth: if it is a rancher authentication
    :param url: URL to reach
    :return: the JSON result
    """
    logging.info('Reaching url : {}'.format(url))
    if basic_auth:
        return requests.get(url, auth=HTTPBasicAuth(ARGS.rancher_access_key, ARGS.rancher_secret_key)).json()

    elif jwt_auth:
        return requests.get(url, headers={'Authorization': 'Bearer {}'.format(token)}).json()

    return requests.get(url).json()


def get_docker_token():
    r = requests.post('https://hub.docker.com/v2/users/login/',
                      data={'username': DOCKER_HUB_USERNAME, 'password': DOCKER_HUB_PASSWORD}).json()
    if 'token' in r:
        return r['token']
    return False


def get_formatted_array_result(results):
    """
    :param results: array of services list per stack
    :return: well formatted array, not dict
    """
    table = [['Stack', 'Service', 'Image', 'Actual tag', 'Latest tag', 'DockerHub']]
    for stack in results:
        display_stack_name = True
        for key, service in enumerate(stack['services']):
            stack_table = []
            if display_stack_name:
                stack_table.append(stack['name'])
            else:
                stack_table.append('')
            stack_table.append(service['name'])
            stack_table.append(service['image'])
            stack_table.append(service['tag'])
            stack_table.append(service['new_tag'])
            stack_table.append('{}/r/{}/tags/'.format(DOCKER_HUB_URL, service['image']))
            table.append(stack_table)
            display_stack_name = False
    return table


def draw_table(results):
    """
    Draw a table into console
    :param results: array of services list per stack
    :return: void
    """
    table = AsciiTable(results)
    print(table.table)


def html_file(results):
    """
    Write an HTML report
    :param results: array of services list per stack
    :return: void
    """
    html_content = ''
    for key, row in enumerate(results):
        if key == 0:
            continue
        html_content += '<tr><th scope="row">{}</th><td>{}</td><td>{}</td><td>{}</td><td>{}</td>'.format(row[0], row[1],
                                                                                                         row[2], row[3],
                                                                                                         row[4])
        html_content += '<td><a target="_blank" href="{}">{}</a></td></tr>'.format(row[5], row[5])

    # Read in the file
    with open(REPORT_FILE_NAME_TEMPLATE, 'r') as file:
        filedata = file.read()

    # Replace the target string
    filedata = filedata.replace('REPORT_GENERATED_HERE', html_content)

    # Write the file out again
    with open(REPORT_FILE_NAME, 'w') as file:
        file.write(filedata)

    file.close()
    webbrowser.open('file://' + os.path.realpath(REPORT_FILE_NAME))


if __name__ == '__main__':
    # Start main process
    logging.info('Start searching with params : \n\t{}'.format(
        '\n\t'.join(['%s:: %s' % (key, value) for (key, value) in vars(ARGS).items()])))
    # Get array of services list per stack
    r = get_formatted_array_result(is_it_the_latest_tag())

    # Draw table with it
    if not ARGS.quiet:
        draw_table(r)

    # Render an HTML table with it
    if ARGS.report:
        html_file(r)
