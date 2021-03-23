#!/usr/bin/python
# encoding: utf-8

# from workflow.notify import notify
from datetime import datetime
import hashlib
import json
import sys
import urllib
import os

from workflow import (Workflow3, ICON_GROUP, ICON_NETWORK, ICON_ACCOUNT,
                      ICON_USER, ICON_INFO, ICON_CLOCK, ICON_WEB, ICON_WARNING,
                      ICON_ERROR)

ICON_ROOT = '/System/Library/CoreServices/CoreTypes.bundle/Contents/Resources'
ICON_IPHONE = os.path.join(ICON_ROOT, 'com.apple.iphone-4-white.icns')
ICON_PHONE = ICON_IPHONE

def ask_ldap(query):
    import ldap3
    srv = ldap3.Server(os.getenv('ldap_url', defaults['ldap_url']))

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

    ldap_basedn = os.getenv('ldap_basedn', defaults['ldap_basedn'])
    log.debug("searching %s in %s" % (query, ldap_basedn))
    search_filter = os.getenv('ldap_filter', defaults['ldap_filter']).format(
                                q=query)

    conn.search(search_base=ldap_basedn, search_filter=search_filter,
                attributes=ldap3.ALL_ATTRIBUTES)
    response = json.loads(conn.response_to_json())

    if (len(response['entries']) < 1):
        wf.add_item(
            title=u"No matches found",
            subtitle=u"Try searching for usernames",
            icon=ICON_WARNING)
        return None

    return response


def main(wf):
    import humanize

    query = None
    if len(wf.args):
        query = wf.args[0]
    else:
        query = "dbewley"

    log.debug("query %s" % query)

    search_results = ask_ldap(query)
    # search_results = wf.cached_data(query, ask_ldap, max_age=3600)
    if not search_results:
        wf.send_feedback()
        return 0

    log.debug(search_results)
    for entry in search_results['entries']:
        e = entry['attributes']
        log.debug("found %s" % e)

        hire_date = (datetime.strptime(
            e['rhatHireDate'].split(' ',)[0], '%Y-%m-%d'))

        gravatar_size = 160
        gravatar_url = "https://www.gravatar.com/avatar/" + \
            hashlib.md5(e['mail'][0].lower()).hexdigest() + "?" + \
            urllib.urlencode({'s': str(gravatar_size)}) + ".jpg"

        mgr_uid=e['manager'][0].split(',')[0].split('=')[1]

        wf.add_item(u'%s' % e['cn'][0],
                    subtitle=u'%s, %s/%s' % (e['title'][0],
                                             e.get('c', ""),
                                             e.get('l', [""])[0]),
                    arg="mailto://%s" % e['mail'][0],
                    quicklookurl=gravatar_url,
                    largetext=u'{cn} {email}\n{title}\n{location} {country}\n'
                            '{costcenter}\nManager: {mgr}'.format(
                                cn=e['cn'][0],
                                title=e.get('title', [""])[0],
                                country=e.get('c', ""),
                                location=e.get('l', [""])[0],
                                email=e['mail'][0],
                                costcenter=e['rhatCostCenterDesc'][0],
                                mgr=mgr_uid
                            ),
                    icon="icon.png",
                    valid=True)

        wf.add_item(u'Tenure',
                    subtitle="Hired {when} by {mgr}".format(
                        when=humanize.naturaltime(hire_date),
                        mgr=mgr_uid),
                    largetext="Hired {ago} on {hired} and\nworks for {mgr}".format(
                        hired=humanize.naturaldate(hire_date),
                        ago=humanize.naturaltime(hire_date, ),
                        mgr=mgr_uid),
                    quicklookurl=gravatar_url,
                    icon=ICON_CLOCK)

        wf.add_item(u'Profile',
                    icon=social_icons['rover'],
                    subtitle="https://rover.redhat.com/people/profile/%s" % e['uid'][0],
                    arg="https://rover.redhat.com/people/profile/%s" % e['uid'][0],
                    valid=True)

        if len(e.get('mobile', [""])[0]):
            wf.add_item(u'Phone',
                        icon=ICON_PHONE,
                        subtitle=e['mobile'][0],
                        arg="tel://%s" % e['mobile'][0],
                        largetext=e['mobile'][0],
                        valid=True)

        wf.add_item(u'Source',
                    icon=social_icons['source'],
                    subtitle="https://source.redhat.com/.profile/%s" % e['uid'][0],
                    arg="https://source.redhat.com/.profile/%s" % e['uid'][0],
                    valid=True)

        if len(e.get('rhatSocialURL', [])):
            for social in e['rhatSocialURL']:
                (site, url) = social.split('->')
                site_icon = ICON_NETWORK
                for social_site in social_icons:
                    if social_site in url.lower():
                        site_icon = social_icons[social_site]

                wf.add_item(site,
                            icon=site_icon,
                            subtitle=url,
                            arg=url,
                            valid=True)

    wf.send_feedback()
    return 0


if __name__ == '__main__':
    defaults = {
        'ldap_url': 'ldap://ldap.corp.redhat.com',
        'ldap_filter': '(&(objectclass=person)(|(uid={q})(sn={q})(mail={q}*)))',
        'ldap_basedn': 'ou=users,dc=redhat,dc=com'
    }
    social_icons = {
        'blog': 'icons/blogger.png',
        'docker': 'icons/registry.png',
        'facebook': 'icons/facebook.png',
        'github': 'icons/github.png',
        'linkedin': 'icons/linkedin.png',
        'quay': 'icons/registry.png',
        'rover': 'icons/rover.png',
        'source': 'icons/opensource.png',
        'twitter': 'icons/twitter.png'
    }
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
