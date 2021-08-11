import re
import os
from datetime import datetime
import dateutil
from constants import MOZILLA_DOMAINS
LDAP_MINIMUM_ACCOUNT_AGE = 7

try:
    from settings import LDAP_MINIMUM_ACCOUNT_AGE
except (ModuleNotFoundError, ImportError):
    pass
try:
    from local_settings import LDAP_MINIMUM_ACCOUNT_AGE
except (ImportError):
    pass



def should_exclude_by_create_date(create_date_obj, delta_days, today_date=None):
    if not today_date:
        today_date = datetime.today()
    try:
        day_delta = today_date - create_date_obj
    except TypeError:
        return False

    return day_delta.days <= delta_days
    

    
def parse_ldap_date(input_date_string):
    try:
        input_date_string = input_date_string.decode()
    except (TypeError, AttributeError):
        pass

    try:
        date_obj = datetime.strptime(input_date_string, "%Y%m%d%H%M%SZ")
    except (AttributeError, ValueError) as e:
        date_obj = None
    return date_obj



def should_exclude_file(uid, name):
    # Taking a uid and name that corresponds to a simple text file
    # 1 uid per line
    # excluded1@domain.com
    # excluded2@domain.com

    filename = "{}_exclusions.txt".format(name)
    dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "exclusions")
    exclude_file_path = os.path.join(dir_path, filename)
    if os.path.exists(exclude_file_path):
        fh = open(exclude_file_path, 'r')
        for entry in fh.readlines():
            entry = entry.strip()
            if entry == uid:
                return True
    return False

def should_exclude_regex(uid, settings):
    # Taking a uid and settings module which includes a list
    # of regex that if a match is successful will return True
    # {
    # 'exclude_regex': [
    #     r'.*_.*'
    # ]
    # }
    for r in settings['exclude_regex']:
        try:
            uid = uid.decode()
        except (AttributeError, TypeError):
            pass

        if re.match(r, uid):
            return True
    return False

def execute_compare(left_entries, right_entries, settings, args):
    left_entries = settings['left_fetcher'](settings)
    right_entries = settings['right_fetcher'](settings)
    messages = []
    # Loop over all the comparisons in settings
    for comp in settings['comparisons']:
        # Start with all entries in the left
        for left_entry in left_entries:
            leftUID = left_entry[settings['leftUID']].encode('utf8')
            should_exclude_by_regex = should_exclude_regex(leftUID, settings)
            should_exclude_by_file = should_exclude_file(leftUID, settings['left_name'])
            if should_exclude_by_regex or should_exclude_by_file:
                continue

            try:
                right_entry = [e for e in right_entries if e[settings['rightUID']] == leftUID][0]
            except (KeyError, IndexError):
                message = "Unable to find entry in {}: {}".format(settings['left_name'], leftUID.decode())
                if not message in messages:
                    messages.append(message)
                continue

            left_attribute = comp['left_attribute']
            right_attribute = comp['right_attribute']
            left_value = left_entry[left_attribute]
            try:
                right_value = [e[right_attribute] for e in right_entries if e[settings['rightUID']] == leftUID][0]
            except (KeyError, IndexError):
                right_value = None
                message = "Unable to find entry in {}: {}".format(settings['right_name'], leftUID.decode())
                if not message in messages:
                    messages.append(message)
            if right_value:
                eval = comp['function'](left_value, right_value, left_entry, right_entry)
                if not eval is True:
                    message = "Incorrect Attribute Match: Account: {} -- {}: {}:{} -- {}: {}:{}".format(settings['left_name'], leftUID, left_attribute, left_value, settings['right_name'], right_attribute, right_value)
                    if not message in messages:
                        messages.append(message)

        # We've already done all of the attribute comparisons, now we just
        # need to make sure nothing is in the right that isn't in the left
        # We're basically going to flip Right -> Left
        for right_entry in right_entries:
            left_entry = right_entry
            leftUID = right_entry[settings['rightUID']].decode()
            # Utilize ability to exclude
            should_exclude_by_regex = should_exclude_regex(leftUID, settings)
            should_exclude_by_file = should_exclude_file(leftUID, settings['right_name'])
            if should_exclude_by_regex or should_exclude_file:
                continue
            try:
                right_entry = [e for e in left_entries if e[settings['leftUID']] == leftUID][0]
            except (KeyError, IndexError):
                message = "Unable to find entry in {}: {}".format(settings['right_name'], leftUID)
                if not message in messages:
                    messages.append(message)

    # For now we just print the messages
    for message in messages:
        print(message)

def compare_workday_ldap(settings, args, workday_entries, ldap_entries):
    execute_compare(workday_entries, ldap_entries, settings, args)

def user_exists_in_ldap_by_mail(ldap_users, mail):
    try:
        return [u for u in ldap_users if u['mail'].decode() == mail][0]
    except (IndexError, KeyError):
        return False

def is_mozilla_email(email):
    for domain in MOZILLA_DOMAINS:
        if domain in email:
            return True
    return False

def extract_mozilla_dynamodb_emails_only(dynamodb_users):
    emails_only = [u['primary_email'] for u in dynamodb_users]
    mozilla_emails = []
    for username in emails_only:
        if is_mozilla_email(username):
            mozilla_emails.append(username)
    return mozilla_emails

def should_exclude_attribute_value(entry, settings):
    # Get exclusions from settings
    # Return False if there are none
    try:
        exclusions = settings['exclude_attribute_value']
    except:
        return False

    for exclusion in exclusions:
        name = exclusion['name']
        value = exclusion['value']
        if entry[name] == value:
            return True
    # Default return False if no matches
    return False


def compare_ldap_auth0(settings, args, ldap_users, auth0_users):
    for entry in auth0_users:
        username = entry['email']
        try:
            last_login = entry['last_login']
        except:
            last_login = ''
        delta_days = 0
        should_exclude_by_file = should_exclude_file(username, settings['left_name'])
        should_exclude_by_regex = should_exclude_regex(username, settings)
        if last_login:
            last_login_obj = dateutil.parser.parse(last_login)
            last_login_obj = datetime.replace(tzinfo=None)
            days_since_login = datetime.today() - last_login_obj
            delta_days = days_since_login.days

        if should_exclude_by_file:
            continue

        if should_exclude_by_regex:
            continue

        if not user_exists_in_ldap_by_mail(ldap_users, username):
            print("Auth0: {} not found in LDAP. Days Since Login: {}".format(username, delta_days))

def compare_ldap_dynamodb(settings, args, ldap_users, dynamodb_users):
    mozilla_only_dynamodb_users = extract_mozilla_dynamodb_emails_only(dynamodb_users)
    for entry in ldap_users:
        username = entry['mail']
        try:
            username = username.decode()
        except (AttributeError, TypeError):
            pass
        should_exclude_by_file = should_exclude_file(username, settings['left_name'])
        should_exclude_by_regex = should_exclude_regex(username, settings)
        create_date = parse_ldap_date(entry['createTimestamp'])
        exclude_by_date = should_exclude_by_create_date(create_date, LDAP_MINIMUM_ACCOUNT_AGE)
        exclude_attribute_value = should_exclude_attribute_value(entry, settings)

        if exclude_by_date:
            continue

        if should_exclude_by_file:
            continue

        if should_exclude_by_regex:
            continue

        if exclude_attribute_value:
            continue

        if not username in mozilla_only_dynamodb_users:
            print("{} not found in DynamoDB.".format(username))

def compare_confluence_ldap(settings, args, confluence_users, ldap_users):
    for entry in confluence_users:
        status = entry['status']
        username = entry['username']
        should_exclude_by_file = should_exclude_file(username, settings['left_name'])
        if should_exclude_by_file:
            continue
        domain_found = is_mozilla_email(username)
        if domain_found and status == 'current':
            if not user_exists_in_ldap_by_mail(ldap_users, username):
                print("{} not found in LDAP.".format(username))

def compare_access_ldap(settings, args, access_entries, ldap_entries):
    for org in access_entries:
        for entry in access_entries[org]:
            # As of now, we just have a list of exclusions
            #should_exclude_by_regex = should_exclude_regex(entry, settings)
            should_exclude_by_file = should_exclude_file(entry, settings['left_name'])
            if should_exclude_by_file:
                continue
            try:
                found = len([u for u in ldap_entries if u[settings['rightUID']] == entry.encode('utf8')]) == 1
            except:
                found = False
            if not found:
                print("{}: needs deactivated in AtlassianAccess for org: {}".format(entry, org))


def process_duplicates(settings):
    messages = []
    entries = settings['fetcher'](settings)
    source_name = settings['name']
    for attribute in settings['duplicates']:
        for entry in entries:
            left_value = entry[attribute]
            address = entry[attribute]
            dupes = len([e for e in entries if e[attribute] == left_value]) > 1
            if dupes:
                message = "{} - Duplicate entry: {} on attribute: {}".format(source_name, address, attribute)
                if not message in messages:
                    messages.append(message)

    # For now we just output we found a dupe.
    for message in messages:
        print(message)