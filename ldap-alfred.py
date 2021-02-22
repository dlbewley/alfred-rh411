#!/usr/bin/env python
# encoding: utf-8

"""
    c: US
    cn: Dale Bewley
    co: USA
    displayName: Dale
    employeeNumber: ######
    employeeType: Employee
    gidNumber: ######
    givenName: Dale
    homeDirectory: /home/remote/dbewley
    l: Sacramento
    loginShell: /bin/bash
    mail: dbewley@redhat.com
    manager: uid=ctjon,ou=users,dc=redhat,dc=com
    memberOf: cn=Employee,ou=userClass,dc=redhat,dc=com
    mobile: +##########
    objectClass: top
                 person
                 organizationalPerson
                 inetOrgPerson
                 rhatPerson
                 posixAccount
                 country
                 friendlyCountry
    postalCode: #####
    preferredTimeZone: America/Los_Angeles
    rhatBJNMeetingID: #########
    rhatBJNUserName: dbewley
    rhatBuildingCode: RMTUSCA
    rhatCostCenter: ###
    rhatCostCenterDesc: CSO Solution Architect-West
    rhatCurrency: USD
    rhatEmployeeSubType: Employee
    rhatGeo: NA
    rhatHireDate: ####-##-## ##:##:##+##:##
    rhatJobCode: ####
    rhatJobTitle: Senior Specialist Solution Architect - Red Hat Integration
    rhatLegalEntity: Red Hat, Inc.
    rhatLocation: Remote US CA
    rhatNickName: dbewley
    rhatOfficeLocation: Remote US CA
    rhatOraclePersonID: ########
    rhatOriginalHireDate: ####-##-## ##:##:##+##:##
    rhatPersonType: Employee
    rhatPreferredLastName: Bewley
    rhatPrimaryMail: dbewley@redhat.com
    rhatSocialURL: Github->https://github.com/dlbewley
                   Linkedin->https://www.linkedin.com/in/dalebewley/
                   Personal->http://guifreelife['com
    rhatSupervisorID: #######
    rhatSupervisorWorkerId: #####
    rhatTeamLead: False
    rhatUUID: #c###eb#-##d#-##ea-###e-#a##ac######
    rhatWorkerId: ######
    sn: Bewley
    st: CA
    street: Return to Red Hat, Raleigh, NC
    title: Senior Specialist Solution Architect
    uid: dbewley
    uidNumber: ######
"""

import sys
import json

from workflow import Workflow3, ICON_GROUP, ICON_NETWORK, ICON_ACCOUNT, ICON_USER, ICON_INFO, ICON_CLOCK, ICON_WEB, ICON_WARNING, ICON_ERROR
from workflow.notify import notify


def ask_ldap(query):
  import ldap3
  srv = ldap3.Server('ldap://ldap.corp.redhat.com')

  try:
    log.debug("connecting to LDAP server")
    conn = ldap3.Connection(srv)
    conn.bind()
  except Exception as err:
    wf.add_item(
            title=u"Unable to connect to LDAP, check VPN",
            subtitle=u"Error: {}".format(err),
            icon=ICON_NETWORK)
    return None

  baseDN='ou=users,dc=redhat,dc=com'
  log.debug("searching %s in %s" % (query, baseDN))
  search_filter='(&(objectclass=person)(uid=%s))' % query

  conn.search(search_base=baseDN, search_filter=search_filter, attributes=ldap3.ALL_ATTRIBUTES)
  response = json.loads(conn.response_to_json())

  if (len(response['entries']) < 1):
    wf.add_item(
            title=u"No matches found",
            subtitle=u"Try searching for usernames",
            icon=ICON_ERROR)
    return None

  return response


def main(wf):
  query = None
  if len(wf.args):
    query = wf.args[0]
  else:
    query = "dbewley"

  log.debug("query %s" % query)

  search_results = ask_ldap(query)
  #search_results = wf.cached_data(query, ask_ldap, max_age=3600)
  if not search_results:
    wf.send_feedback()
    return 0

  log.debug(search_results)
  for entry in search_results['entries']:
    e = entry['attributes']
    log.debug("found %s" % e)

    wf.add_item(u'Rover',
            icon=ICON_INFO,
            subtitle="https://rover.redhat.com/people/profile/%s" % e['uid'][0],
            arg="https://rover.redhat.com/people/profile/%s" % e['uid'][0],
            largetext=u'{cn}\n{title}\n{country} {location}\n{email}\nCost center: {costcenter}, Manager: {mgr}'.format(
                cn=e['cn'][0],
                title=e['title'][0],
                country=e['c'][0],
                location=e['l'][0],
                email=e['mail'][0],
                costcenter=e['rhatCostCenterDesc'][0],
                mgr=e['manager'][0].split(',')[0].split('=')[1]
            ),
            valid=True)

    wf.add_item(u'%s' % e['cn'][0],
            icon=ICON_USER,
            subtitle=u'%s, %s/%s' % (e['title'][0],
                                    e['c'][0],
                                    e['l'][0]),
            arg="mailto://%s" % e['mail'][0],
            valid=True)

    wf.add_item(u'Phone',
            icon=ICON_USER,
            subtitle=e['mobile'][0],
            arg="tel://%s" % e['mobile'][0],
            largetext=e['mobile'][0],
            valid=True)

    wf.add_item(u'Source',
            icon=ICON_NETWORK,
            subtitle="https://source.redhat.com/.profile/%s" % e['uid'][0],
            arg="https://source.redhat.com/.profile/%s" % e['uid'][0],
            valid=True)

    if len(e['rhatSocialURL']):
        for social in e['rhatSocialURL']:
            (site, url) = social.split('->')
            wf.add_item(site,
                    icon=ICON_NETWORK,
                    subtitle=url,
                    arg=url,
                    valid=True)

  wf.send_feedback()
  return 0


if __name__ == '__main__':
    # Create a global `Workflow3` object
    wf = Workflow3(
            libraries=['./lib'],
            update_settings={
                'github_slug': 'dlbewley/alfred-rh411',
                'frequency': 7
            }
            )
    log = wf.logger

    if wf.update_available:
      wf.add_item('New version available',
                  'Action this item to install the update',
                  autocomplete='workflow:update',
                  icon=ICON_INFO)
    sys.exit(wf.run(main))
