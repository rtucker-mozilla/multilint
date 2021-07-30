import re
import os
from constants import MOZILLA_DOMAINS

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
            if should_exclude_by_regex or should_exclude_file:
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
        for ldap_entry in right_entries:
            left_entry = ldap_entry
            leftUID = ldap_entry[settings['rightUID']].decode()
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

def compare_confluence_ldap(settings, args, confluence_users, ldap_users):
    for entry in confluence_users:
        status = entry['status']
        username = entry['username']
        should_exclude_by_file = should_exclude_file(entry, settings['left_name'])
        if should_exclude_by_file:
            continue
        domain_found = False
        for domain in MOZILLA_DOMAINS:
            if domain in username:
                domain_found = True
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