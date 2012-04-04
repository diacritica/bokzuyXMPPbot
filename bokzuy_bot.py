#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    bokzuyXMPPbot: Your dummy XMPP bot for Bokzuy.com
    Copyright (C) 2012 Pablo Ruiz Múzquiz

    See the file LICENSE for copying permission.
"""

import sys
import logging
import getpass
import json
import sleekxmpp

import requests

from optparse import OptionParser


# Make sure we use UTF-8 by default even with python < 3.0.
if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')
else:
    raw_input = input


class EchoBot(sleekxmpp.ClientXMPP):

    """
    A simple SleekXMPP bot for Bokzuy that will follow orders
    such as listing friends, badges and sending bokies.
    Based on the SleekXMPP bot.
    """

    def __init__(self, jid, password,bokzuy_auth):

        sleekxmpp.ClientXMPP.__init__(self, jid, password)
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message)

        self.bokzuy_auth = bokzuy_auth

    def start(self, event):

        self.send_presence()
        self.get_roster()

    def message(self, msg):
        """
        Process incoming message stanzas. Be aware that this also
        includes MUC messages and error messages. It is usually
        a good idea to check the messages's type before processing
        or sending replies.

        Arguments:
            msg -- The received message stanza. See the documentation
                   for stanza objects and the Message stanza to see
                   how it may be used.
        """
        if msg['type'] in ('chat', 'normal'):

            msgstr = "%(body)s" %msg
            if msgstr == "b":
                result = self.get_badges()
                resultdict = json.loads(result)
                resultlist = ["%i - %s"%(badge["id"],badge["name"]) for badge in resultdict["badges"]]
                resultlist.sort()
                resultstr = "\n".join(resultlist)

            elif msgstr == "f":
                result = self.get_friends()
                resultdict = json.loads(result)
                resultlist = ["%i - %s"%(friend[u"id"],friend[u"name"]) for friend in resultdict[u"friends"]]
                resultlist.sort()
                resultstr = "\n".join(resultlist)

            else:
                try:
                    if msgstr.count("@") == 3: 
                        badgeid,userid,comment,group = msgstr.split("@")
                    else:
                        group = ""
                        badgeid,userid,comment = msgstr.split("@")
                    result = self.send_boky(int(badgeid),int(userid),comment,group)
                    resultstr=json.loads(result)["msg"]
                except:
                    resultstr = "This bot is away or you made a mistake"


            msg.reply(resultstr).send()


    def send_boky(self,badgeid=1,userid=10, comment="API TEST THROUGH XMPP BOT :)",group="kaleidos"):


        params = {
            'badgeId':badgeid,
            'comment':comment,
            'group':group,
        }

        response = requests.post("https://api.bokzuy.com/%s/bokies"%(userid), data=params, auth=self.bokzuy_auth, verify=False)
        return response.content

    def get_badges(self):
        response = requests.get("https://api.bokzuy.com/badges",auth=self.bokzuy_auth, verify=False)

        return response.content

    def get_friends(self):
        response = requests.get("https://api.bokzuy.com/me/friends",auth=self.bokzuy_auth, verify=False)

        return response.content


if __name__ == '__main__':
    # Setup the command line arguments.
    optp = OptionParser()

    # Output verbosity options.
    optp.add_option('-q', '--quiet', help='set logging to ERROR',
                    action='store_const', dest='loglevel',
                    const=logging.ERROR, default=logging.INFO)
    optp.add_option('-d', '--debug', help='set logging to DEBUG',
                    action='store_const', dest='loglevel',
                    const=logging.DEBUG, default=logging.INFO)
    optp.add_option('-v', '--verbose', help='set logging to COMM',
                    action='store_const', dest='loglevel',
                    const=5, default=logging.INFO)

    # JID and password options.
    optp.add_option("-j", "--jid", dest="jid",
                    help="JID to use")
    optp.add_option("-p", "--password", dest="password",
                    help="password to use")

    # Bokzuy user and password options.
    optp.add_option("-b", "--bokid", dest="bokzuy_username",
                    help="Bokzuy user to use")
    optp.add_option("-w", "--bokpass", dest="bokzuy_password",
                    help="Bokzuy password to use")


    opts, args = optp.parse_args()

    # Setup logging.
    logging.basicConfig(level=opts.loglevel,
                        format='%(levelname)-8s %(message)s')

    if opts.jid is None:
        opts.jid = raw_input("Username: ")
    if opts.password is None:
        opts.password = getpass.getpass("Password: ")

    if opts.bokzuy_username is None:
        opts.bokzuy_username = raw_input("Bokzuy username: ")
    if opts.bokzuy_password is None:
        opts.bokzuy_password = getpass.getpass("Bokzuy password: ")

    bokzuy_auth = (opts.bokzuy_username, opts.bokzuy_password)

    xmpp = EchoBot(opts.jid, opts.password, bokzuy_auth)
    xmpp.register_plugin('xep_0030') # Service Discovery
    xmpp.register_plugin('xep_0004') # Data Forms
    xmpp.register_plugin('xep_0060') # PubSub
    xmpp.register_plugin('xep_0199') # XMPP Ping


    if xmpp.connect(('talk.google.com', 5222)):

        #xmpp.process(block=True)
        
        xmpp.process(threaded=False)
        print("Done!")
    else:
        print("Unable to connect.")
