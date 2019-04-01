# inout
In-out Checker: Bluetooth detection script for Raspberry PI

# Overview
This script will detect the presence of Bluetooth devices by Raspberry PI.

When a Bluetooth device is detected or out of the range of Raspberry PI, this script writes the date and time into
Google Spreadsheet.

# Install
1. Copy the following In-Out Checker Google Spreadsheet template to your Google Spreadsheet.

   https://docs.google.com/spreadsheets/d/1Mk71lyJhDoBiPQiiNaIn-cQ-KnqVbd49oVlabT_O2FI

2. Modify `scripts/inout.json`

   ```
   ${DEVICE_ID_N}: Replace to your Bluetooth Device ID
   ${SHEET_ID_N}: Your Google Spreadsheet ID
   ${SHEET_SOURCE_ID_N}: The template sheet ID (from the above sheet named YYYY-MM)
   ```

   (`scripts/inout.json` example)

   ```
   {
     "DEVICES": [
     {
       "DEVICE_ID": '34:18:BF:5B:22:31',
       "SPREADSHEETS": {"4gJuW03418G6KOymH4Z-9uGT-xNP6mbhINbuQ-XR1H22": "1567910069"}
     },
     {
       "DEVICE_ID": '34:18:BF:5B:22:32',
       "SPREADSHEETS": {"4gJuW03418G6KOymH4Z-9uGT-xNP6mbhINbuQ_XR1H22": "1567910069"}
     }
   ]}
   ```

3. Modify `install.sh`.  Enter your `CLIENT_ID`, `PROJECT_ID` and `CLIENT_SECRET` for Google Spreadsheet API. 

   ```
   export CLIENT_ID="<ENTER_YOUR_CLIENT_ID>"
   export PROJECT_ID="<ENTER_PROJECT_ID>"
   export CLIENT_SECRET="<ENTER_YOUR_CLIENT_SECRET>"
   ```

4. Run `chmod +x install.sh; ./install.sh`