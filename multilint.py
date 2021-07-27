import argparse
import settings
from runners import compare_workday_ldap, process_duplicates, compare_access_ldap
from fetchers import cis, ldap, access



def main():
    parser = argparse.ArgumentParser()
    #parser.add_argument('commit', help='whether to commit or not', action='store')
    args = parser.parse_args()
    ldap_users = ldap(settings)
    access_users = access(settings, active_only=True)
    compare_access_ldap(settings, args, access_users, ldap_users)

    # Placeholder for which arguments we end up using. --commit is a standardf
    #cis(settings, '')
    #compare_workday_ldap(settings.workday_ldap, args)
    #process_duplicates(settings.workday)
    #process_duplicates(settings.ldap)

if __name__ == '__main__':
    main()
	