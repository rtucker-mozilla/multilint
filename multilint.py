import argparse
import settings
from runners import compare_workday_ldap, process_duplicates, compare_access_ldap
from fetchers import cis, ldap, access



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('access-ldap', help='', action='store_true')
    parser.add_argument('workday-ldap', help='', action='store_true')
    args = parser.parse_args()
    workday_users = None
    ldap_users = None
    access_users = None

    if args.access_ldap:
        if ldap_users is None:
            ldap_users = ldap(settings)
        if access_users is None:
            access_users = access(settings, active_only=True)
        compare_access_ldap(settings.access_ldap, args, access_users, ldap_users)

    if args.workday_ldap:
        if ldap_users is None:
            ldap_users = ldap(settings)
        # Need to refactor this to accept ldap_users and workday_users as
        # arguments
        #compare_workday_ldap(settings.workday_ldap, args)
    
    # Placeholder for which arguments we end up using. --commit is a standardf
    #cis(settings, '')
    #process_duplicates(settings.workday)
    #process_duplicates(settings.ldap)

if __name__ == '__main__':
    main()
	