import argparse
import settings
from runners import compare_workday_ldap, process_duplicates, compare_access_ldap
from runners import compare_confluence_ldap
from fetchers import cis, confluence, ldap, access, workday



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--access-ldap', help='', action='store_true')
    parser.add_argument('--workday-ldap', help='', action='store_true')
    parser.add_argument('--confluence-ldap', help='', action='store_true')
    args = parser.parse_args()
    workday_users = None
    ldap_users = None
    access_users = None
    confluence_users = None

    if args.access_ldap:
        if ldap_users is None:
            ldap_users = ldap(settings)
        if access_users is None:
            access_users = access(settings, billable_only=True)
        compare_access_ldap(settings.access_ldap, args, access_users, ldap_users)

    if args.workday_ldap:
        if ldap_users is None:
            ldap_users = ldap(settings)
        if workday_users is None:
            workday_users = workday(settings)
        compare_workday_ldap(settings.workday_ldap, args, workday_users, ldap_users)
        
    if args.confluence_ldap:
        if ldap_users is None:
            ldap_users = ldap(settings)
        if confluence_users is None:
            confluence_users = confluence(settings)
        compare_confluence_ldap(settings.confluence_ldap, args, confluence_users, ldap_users)
    
    #cis(settings, '')
    #process_duplicates(settings.workday)
    # Probably not necessary since we've added an overlap to stop dupes
    #process_duplicates(settings.ldap)

if __name__ == '__main__':
    main()
	