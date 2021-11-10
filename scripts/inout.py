#!/usr/bin/python
# -*- coding: utf-8 -*-

# updated by yas 2021/11/09
# updated by yas 2019/03/01
# updated by yas 2019/02/07
# updated by yas 2019/02/03
# updated by yas 2019/01/30
# updated by yas 2019/01/29
# updated by yas 2019/01/28
# updated by yas 2019/01/27
# updated by yas 2017/10/19
# updated by yas 2017/08/07
# updated by yas 2017/07/11
# updated by yas 2017/07/10
# updated by yas 2017/07/05
# updated by yas 2017/01/26
# updated by yas 2017/01/24
# updated by yas 2017/01/10
# updated by yas 2017/01/09
# updated by yas 2017/01/03
# updated by yas 2016/12/27
# created by yas 2016/12/26

from __future__ import print_function
import httplib2
import os
import time
import datetime
import bluetooth
import yaml

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage


def _get_first_working_day_of_month(date=None):
    """Return the first working date of the month"""

    if not date:
        date = datetime.date.today()

    # Saturday YYYY-MM-03
    # Saturday YYYY-MM-03
    # M-F      YYYY-MM-01
    return date.replace(day=3) if (date.weekday == 6) else date.replace(day == 2) if (
            date.weekday == 0) else date.replace(day=1)


class InOut(object):
    SLEEP_INTERVAL = 20
    FIRST_ROW = 3
    SERVICE = None
    FLAGS = False
    DEVICES = []

    """
    If modifying these scopes, delete your previously saved credentials
    at ~/.credentials/sheets.googleapis.com-python-quickstart.json
    SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
    """
    SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
    CLIENT_SECRETS_FILE = 'client_secrets.json'
    APPLICATION_NAME = 'Google Sheets API Python Inout Client'

    def __init__(self):
        try:
            import argparse
            self.FLAGS = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()

        except ImportError:
            self.FLAGS = None

        self.SERVICE = self.get_service()
        if self.SERVICE is None:
            print('In-Out (__init__): No service found.')
            exit()

        yaml_file = os.path.splitext(os.path.basename(__file__))[0] + '.yaml'
        if not os.path.exists(yaml_file):
            print('Not found: ' + yaml_file)
            exit()

        try:
            with open(yaml_file, 'r') as conf:
                self.DEVICES = yaml.safe_load(conf)['DEVICES']

        except:
            print('Could not open: ' + yaml_file)

    def get_credentials(self):
        """Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns:
            Credentials, the obtained credential.
        """

        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,
                                       'sheets.googleapis.com-python-inout.json')
        store = Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(self.CLIENT_SECRETS_FILE, self.SCOPES)
            flow.user_agent = self.APPLICATION_NAME
            if self.FLAGS:
                credentials = tools.run_flow(flow, store, self.FLAGS)
            else:  # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, store)
            print('In-Out: Storing credentials to ' + credential_path)
        return credentials

    def get_service(self):

        # Creates a Sheets API service object
        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        try:
            discovery_url = ('https://sheets.googleapis.com/$discovery/rest?'
                             'version=v4')
            return discovery.build('sheets', 'v4', http=http,
                                   discoveryServiceUrl=discovery_url)
        except Exception as e:
            print('In-Out: Error: Authentication')
            print(e)
            print('Exiting...')
            exit()
            # return None

    def run(self):

        # while True: # Don't loop since systemd will take care of daemonize

        print('In-Out: Checking ' + time.strftime('%Y/%m/%d (%a) %H:%M %Z', time.localtime()))

        for device in self.DEVICES:

            spreadsheets = device['SPREADSHEETS']
            for spreadsheet_id in spreadsheets.keys():

                # Write a time at "Last Update" (A2:A2)
                try:
                    # YYYY-MM-DD
                    range_name = '%s!A1:A1' % (time.strftime('%Y-%m', time.localtime()))
                    body = {'values': [[time.strftime('%Y/%m/%d', time.localtime())]]}
                    self.SERVICE.spreadsheets().values().update(
                        spreadsheetId=spreadsheet_id, range=range_name,
                        valueInputOption=u'USER_ENTERED', body=body).execute()

                    # HH:mm
                    range_name = '%s!A2:A2' % (time.strftime('%Y-%m', time.localtime()))
                    body = {'values': [[time.strftime('%H:%M', time.localtime())]]}
                    self.SERVICE.spreadsheets().values().update(
                        spreadsheetId=spreadsheet_id, range=range_name,
                        valueInputOption=u'USER_ENTERED', body=body).execute()

                except:

                    self._create_sheet(spreadsheet_id=spreadsheet_id,
                                       sheet_source_id=spreadsheets[spreadsheet_id])

            # print('Searching...: ' + device['DEVICE_ID'])
            result = bluetooth.lookup_name(device['DEVICE_ID'], timeout=5)
            if result is not None:
                print('In-Out: In: %s (%s)' % (result, device['DEVICE_ID']))
                self.write_in_out(device=device)
                # return  # Skip the remaining device check
            else:
                print('In-Out: No Bluetooth device detected: ' + device['DEVICE_ID'])

    # time.sleep(self.SLEEP_INTERVAL)

    def write_in_out(self, device=None):

        if device is None:
            device = {}
        for spreadsheet_id in device['SPREADSHEETS'].keys():
            try:
                range_name = '%s!A%s:D35' % (time.strftime('%Y-%m', time.localtime()), self.FIRST_ROW)
                result = self.SERVICE.spreadsheets().values().get(
                    spreadsheetId=spreadsheet_id, range=range_name).execute()
                values = result.get('values', [])

            except:

                return

            if not values:

                print('In-Out: No data found.')

            else:

                # print('=================')
                # print(result)

                sheet_name = time.strftime('%Y-%m', time.localtime())
                body = {'values': [[time.strftime('%H:%M', time.localtime())]]}

                i = self.FIRST_ROW
                for row in values:
                    # print('In-Out: %s | %s ' % (row[0], i))
                    if time.strftime('%Y-%m-%d', time.localtime()) == row[0]:

                        # Write the time at an 'in' column is empty
                        if len(row) < 3:
                            try:
                                range_name = '%s!C%s' % (sheet_name, i)
                                print('In-Out: Wrote: range_name: %s | %s | body: %s' % (
                                    range_name, time.strftime('%Y-%m-%d', time.localtime()), body))
                                self.SERVICE.spreadsheets().values().update(
                                    spreadsheetId=spreadsheet_id, range=range_name,
                                    valueInputOption=u'USER_ENTERED', body=body).execute()

                            except:
                                print('In-Out: Error: write_in_out: (in) self.SERVICE.spreadsheets().values().update()')

                        try:
                            # Always write the time at an 'out' column while the bluetooth device is detected
                            range_name = '%s!D%s' % (sheet_name, i)
                            print('In-Out: Wrote: range_name: %s | %s | body: %s' % (
                                range_name, time.strftime('%Y-%m-%d', time.localtime()), body))
                            self.SERVICE.spreadsheets().values().update(
                                spreadsheetId=spreadsheet_id, range=range_name,
                                valueInputOption=u'USER_ENTERED', body=body).execute()

                        except:
                            print('In-Out: Error: write_in_out: (out) self.SERVICE.spreadsheets().values().update()')

                    i = i + 1

    def _create_sheet(self, spreadsheet_id='', sheet_source_id=''):

        # Create a new spreadsheet
        sheet_name = time.strftime('%Y-%m', time.localtime())
        try:

            body = {'requests': [{
                'duplicateSheet': {
                    'newSheetName': sheet_name,
                    'insertSheetIndex': 0,
                    'sourceSheetId': sheet_source_id,
                }
            }]}

            self.SERVICE.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id, body=body).execute()

            body = {'values': [[_get_first_working_day_of_month().strftime('%Y-%m-%d')]]}
            range_name = '%s!A%s' % (sheet_name, self.FIRST_ROW)
            self.SERVICE.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id, range=range_name,
                valueInputOption=u'USER_ENTERED', body=body).execute()

            print('In-Out: Created new Spreadsheet: %s' % sheet_name)

        except Exception as e:

            print('In-Out: Error: _create_sheet: %s' % sheet_name)
            print(e)


if __name__ == '__main__':
    InOut().run()
