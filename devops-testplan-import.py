import argparse
import getpass
import csv

from xml.etree.ElementTree import Element, SubElement, Comment, tostring
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication

class PAT:
    DEFAULT = 'Prompt if not specified'

    def __init__(self, value):
        if value == self.DEFAULT:
            value = getpass.getpass('Personal Access Token (PAT): ')
        self.value = value

    def __str__(self):
        return self.value

def parse_steps(steps_raw):
    # Generate raw XML from these test steps
    # <steps id="0" last="1">
    #     <step id="1" type="ValidateStep">
    #         <parameterizedString isformatted="false">Action 1</parameterizedString>
    #         <parameterizedString isformatted="false"></parameterizedString>
    #         <description />
    #     </step>
    # </steps>
    steps = Element('steps')
    steps.set('id', '0')
    steps.set('last', '1')

    step = SubElement(steps, 'step')
    step.set('id', '1')
    step.set('type', 'ValidateStep')
    parameterizedString = SubElement(step, 'parameterizedString')
    parameterizedString.text = steps_raw
    parameterizedString.set('isformatted', 'false')
    parameterizedString = SubElement(step, 'parameterizedString')
    parameterizedString.text = ''
    parameterizedString.set('isformatted', 'false')
    description = SubElement(step, 'description')

    return str(tostring(steps),'utf8')

def build_test_case_document(title, state, area_path, iteration_path, priority, description, steps):
    return [
    {
        "op": "add",
        "path": "/fields/System.Title",
        "value": title
    },
    {
        "op": "add",
        "path": "/fields/System.State",
        "value": state
    },
    {
        "op": "add",
        "path": "/fields/System.AreaPath",
        "value": area_path
    },
    {
        "op": "add",
        "path": "/fields/System.IterationPath",
        "value": iteration_path
    },
    {
        "op": "add",
        "path": "/fields/Microsoft.VSTS.Common.Priority",
        "value": priority
    },
    {
        "op": "add",
        "path": "/fields/System.Description",
        "value": description
    },
    {
        "op": "add",
        "path": "/fields/Microsoft.VSTS.TCM.Steps",
        "value": parse_steps(steps)
    }
    ]

def create_work_items(personal_access_token=None, organisation=None, filename=None, project=None):
    organisation_url = 'https://dev.azure.com/{}'.format(organisation)

    # Create a connection to the org
    credentials = BasicAuthentication('', personal_access_token)
    connection = Connection(base_url=organisation_url, creds=credentials)

    # Create a client to write test cases as work items
    work_item_client = connection.clients.get_work_item_tracking_client()

    # Open the CSV file
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile)
        for testcase in reader:
            document = build_test_case_document(
                testcase["Title"], 
                testcase["State"],
                testcase["Area Path"], 
                testcase["Iteration Path"], 
                testcase["Priority"],
                testcase["Description"],
                testcase["Steps"])
            work_item = work_item_client.create_work_item(document, project, testcase['Work Item Type'], suppress_notifications=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--org', help='Azure DevOps Organisation, e.g dev.azure.com/{org}', required=True)
    parser.add_argument('-i', '--project', help='Project to import Work Items into', required=True)
    parser.add_argument('-p', '--pat', type=PAT, help='Personal access token for authentication',
        default=PAT.DEFAULT)
    parser.add_argument('-f', '--filename', help='CSV file to import work items from', required=True)
    args = parser.parse_args()
    create_work_items(personal_access_token=args.pat, organisation=args.org, filename=args.filename, project=args.project)