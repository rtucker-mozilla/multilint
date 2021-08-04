from local_settings import CIS_GRANT_TYPE, CIS_SCOPE, WORKDAY_FULL_SYNC_URL, WORKDAY_USER, WORKDAY_PASS, PROXIES # type: ignore
from local_settings import LDAP_HOST, LDAP_USER, LDAP_PASSWORD # type: ignore
from local_settings import CIS_TOKEN_URL, CIS_AUDIENCE, CIS_CLIENT_ID, CIS_SECRET, CIS_BASE_URL
from local_settings import CONFLUENCE_BASE_URL, CONFLUENCE_USERNAME, CONFLUENCE_PASSWORD
from local_settings import ACCESS_ORGS, ACCESS_TOKEN
from local_settings import DYNAMODB_PROFILE_NAME, DYNAMODB_TABLE_NAME, DYNAMODB_REGION_NAME, DYNAMODB_SCAN_ARGS, DYNAMODB_CACHEFILE_NAME 
from constants import MOZILLA_DOMAINS
import requests
import json
import boto3

# For fetchers we may need to maintain a database of when the data was retrieved
# Due to different timeframes of data sync, we won't always want to compare the most recent
# Initially though, live data compare will be ok

def extract_by_mozilla_domains(users):
    return_users = []
    for user in users:
        for domain in MOZILLA_DOMAINS:
            if domain in user['primary_email']:
                return_users.append(user)
    emails = set([u['primary_email'] for u in users])
    for email in emails:
        email_count = len([u for u in users if u['primary_email'] == email])
        if email_count > 1:
            print("Dupe found for email: {}".format(email))

def filter_access_lists(org_lists, return_attribute, k, v):
    ret = {}
    for org in org_lists:
        ret[org] = [u[return_attribute] for u in org_lists[org] if u[k] == v]
    return ret


def dynamodb(table, from_cache=False):
    if from_cache:
        try:
            fh = open(DYNAMODB_CACHEFILE_NAME, 'rb')
            b_data = fh.read()
            r_data = json.loads(b_data)
            fh.close()
            return r_data
        except TypeError:
            return []
    ret = []
    done = False
    start_key = None
    scan_kwargs = {
        'ProjectionExpression': DYNAMODB_SCAN_ARGS
    }
    table_name = DYNAMODB_TABLE_NAME
    session = boto3.Session(profile_name=DYNAMODB_PROFILE_NAME, region_name=DYNAMODB_REGION_NAME)
    table = session.resource('dynamodb').Table(table_name)
    while not done:
        if start_key:
            scan_kwargs['ExclusiveStartKey'] = start_key
        response = table.scan(**scan_kwargs)
        if response['Count'] > 0:
            for item in response.get('Items'):
                ret.append(item)
        start_key = response.get('LastEvaluatedKey', None)
        done = start_key is None
    fh = open(DYNAMODB_CACHEFILE_NAME , "wb")
    fh.write(json.dumps(ret).encode("utf8"))
    fh.close()
    return ret

def confluence(settings):
    done = False
    confluence_users = []
    url = "{}/rest/api/group/everyone/member?expand=status".format(CONFLUENCE_BASE_URL)
    while not done:
        resp = requests.get(url, proxies=PROXIES, auth=(CONFLUENCE_USERNAME, CONFLUENCE_PASSWORD))
        confluence_users += resp.json()['results']
        try:
            next = resp.json()['_links']['next']
            url = "{}{}".format(CONFLUENCE_BASE_URL, next)
        except KeyError:
            done = True
    return confluence_users

def access(settings, billable_only=False, active_only=False):
    headers = {
        'Accept': 'application/json',
        'Authorization': 'Bearer {}'.format(ACCESS_TOKEN),
    }
    ret = {}
    done = False
    for org in ACCESS_ORGS:
        ret[org] = []
        url = "https://api.atlassian.com/admin/v1/orgs/{}/users".format(org)
        while not done:
            resp = requests.get(url, headers=headers, proxies=PROXIES)
            ret[org] += resp.json()['data']
            try:
                url = resp.json()['links']['next']
                if not len(url) > 0:
                    done = True
            except:
                done = True
        if active_only:
            return filter_access_lists(ret, 'email', 'account_status', 'active')
        elif billable_only:
            return filter_access_lists(ret, 'email', 'access_billable', True)
        else:
            return ret


def cis(settings, query_url):
    auth_data = {
        "audience": CIS_AUDIENCE,
        "scope": CIS_SCOPE,
        "grant_type": CIS_GRANT_TYPE,
        "client_id": CIS_CLIENT_ID,
        "client_secret": CIS_SECRET
    }
    headers = {
        'Content-Type': 'application/json'
    }

    token_resp = requests.post(CIS_TOKEN_URL, proxies=PROXIES, headers=headers, data=json.dumps(auth_data)) # pragma: no cover
    try:
        token = token_resp.json()['access_token']
    except KeyError:
        token = None
    if token:
        query_headers = {
            "Authorization": 'Bearer {}'.format(token)
        }
        query_resp = requests.get("https://person.api.sso.mozilla.com/v2/users/id/all?connectionMethod=ad&active=true", headers=query_headers)
        try:
            users = query_resp.json()['users']
        except KeyError:
            users = None
        mozilla_users = extract_by_mozilla_domains(users)


def workday(settings):
    # Here we will actually talk to the API and retrive all entries
    # Constructing a JSON response similar to what is in mock_workday
    resp = requests.get(WORKDAY_FULL_SYNC_URL, auth=(WORKDAY_USER, WORKDAY_PASS), proxies=PROXIES) # pragma: no cover
    return_value = resp.json()['Report_Entry']
    return return_value

def ldap(settings):
    import ldap as ldaplib # type: ignore
    # Here we will actually talk to LDAP
    # Constructing a JSON response similar to what is in mock_ldap
    ldap_attrs = [
        'mail',
        'employeeNumber',
        'workdayCostCenter',
        'employeeType'
    ]
    ldap_conn = ldaplib.initialize(LDAP_HOST) # pragma: no cover
    ldap_conn.start_tls_s()
    ldap_conn.simple_bind_s(LDAP_USER, LDAP_PASSWORD)
    members = ldap_conn.search_s('dc=mozilla',
                ldaplib.SCOPE_SUBTREE,
                '(&(objectClass=mozComPerson)(mail=*))',
                attrlist=ldap_attrs)
    return_list = []
    for member in members:
        tmp = {}
        tmp['dn'] = str(member[0])
        for k in member[1].keys():
            if type(member[1][k]).__name__ == 'list':
                tmp[k] = member[1][k][0]
            else:
                tmp[k] = str(member[1][k])
        return_list.append(tmp)
    return return_list

def mock_workday(settings):
    return [
        {
        'PrimaryWorkEmail': 'match@domain.com',
        'EmployeeNumber': 'E123456'
        },
        {
        'PrimaryWorkEmail': 'nomatch@domain.com',
        'EmployeeNumber': '123'
        },
        {
        'PrimaryWorkEmail': 'nomatch2@domain.com',
        'EmployeeNumber': '123'
        },
        {
        'PrimaryWorkEmail': 'nomatch2@domain.com',
        'EmployeeNumber': '123'
        },
        {
        'PrimaryWorkEmail': 'notfoundinldap@domain.com',
        'EmployeeNumber': '1234567'
        },
    ]

def mock_ldap(settings):
    return [
        {
        'mail': 'match@domain.com',
        'workdayEmployeeNumber': 'E123456'
        },
        {
        'mail': 'nomatch@domain.com',
        'workdayEmployeeNumber': '456'
        },
        {
        'mail': 'notinworkday@domain.com',
        'workdayEmployeeNumber': 'a9999'
        },
    ]

#workday({})
#ldap({})
