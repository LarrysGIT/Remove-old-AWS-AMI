from __future__ import print_function

# Larry created on 2017-07-03
'''
Set below 3 environment variables to work
AMI_LOOKUP_PATTERN: TEMPLATE_2016_Larry_*
FORCE_KEEP_AMIS: 5
REMOVE_OLDER_THAN_X_DAYS: 90

Add more patterns like below,
AMI_LOOKUP_PATTERN2: ThisIsAAMIPattern*
AMI_LOOKUP_PATTERN3: ThisIsAAMIPattern_v20_*
'''

import boto3
import os
import json
import re
import time
from datetime import datetime
from operator import itemgetter
import logging

def lambda_handler(event, context):
    logging.getLogger().setLevel(logging.INFO)
    logging.info('Old AMI auto removal triggered')

    # AMI automatic lookup pattern
    # If AMI_LOOKUP_PATTERN not set, script not be able to search AMI
    AMI_LOOKUP_PATTERNS = [ os.environ[i] for i in os.environ.keys() if re.search('^AMI_LOOKUP_PATTERN\d*', i) ]
    AMI_LOOKUP_PATTERNS = [ i.strip() for i in AMI_LOOKUP_PATTERNS if i.strip() ]

    # Restrict AMI_LOOKUP_PATTERN
    for AMI_LOOKUP_PATTERN in AMI_LOOKUP_PATTERNS:
        if len(AMI_LOOKUP_PATTERN) < 15 or AMI_LOOKUP_PATTERN.count('*') > 2:
            logging.info('Please restrict AMI_LOOKUP_PATTERN')
            return 'Function refuse to run'

    # AMIs older than X days to remove
    REMOVE_OLDER_THAN_X_DAYS = os.getenv('REMOVE_OLDER_THAN_X_DAYS')
    if re.search('^\d+$', REMOVE_OLDER_THAN_X_DAYS):
        REMOVE_OLDER_THAN_X_DAYS = int(REMOVE_OLDER_THAN_X_DAYS)
    else:
        return 'REMOVE_OLDER_THAN_X_DAYS is not valid int number'

    # At least X AMIs to keep
    FORCE_KEEP_AMIS = os.getenv('FORCE_KEEP_AMIS')
    if re.search('^\d+$', FORCE_KEEP_AMIS):
        FORCE_KEEP_AMIS = int(FORCE_KEEP_AMIS)
    else:
        return 'FORCE_KEEP_AMIS is not valid int number'

    logging.info('Remove amis older than [%s] days and force keep at least [%s] amis' % (REMOVE_OLDER_THAN_X_DAYS, FORCE_KEEP_AMIS))

    now = datetime.utcnow()
    for AMI_LOOKUP_PATTERN in AMI_LOOKUP_PATTERNS:
        logging.info(' ****** Processing {}'.format(AMI_LOOKUP_PATTERN))
        amis = []
        amis = lookup_amis(LookupPattern=AMI_LOOKUP_PATTERN)
        logging.info('Images found: %s' % len(amis))
        for i in amis:
            logging.info('Image: [Name:%s][Id:%s][CreationTime:%s]' % (i['Name'], i['ImageId'], i['CreationDate']))
        old_amis = []
        for i in amis:
            try:
                ami_CreationTime = datetime.strptime(i['CreationDate'], '%Y-%m-%dT%H:%M:%S.%fZ')
                time_diff = now - ami_CreationTime
                logging.info('AMI ID: %s, Creation date: %s, Gap to now: %s' % (i['ImageId'], i['CreationDate'], str(time_diff)))
                if time_diff.days > REMOVE_OLDER_THAN_X_DAYS:
                    logging.info('AMI [%s] older than [%s] days' % (i['ImageId'], REMOVE_OLDER_THAN_X_DAYS))
                    if len(amis) - len(old_amis) > FORCE_KEEP_AMIS:
                        old_amis.append(i)
                        logging.info('AMI [%s] marked as deregister' % i['ImageId'])
                    else:
                        logging.info('At least keep %s AMIs, ' % FORCE_KEEP_AMIS)
            except Exception as e:
                logging.error('Failed to convert creation date of %s' % i['ImageId'])
                logging.error(str(e))
                pass
        if old_amis:
            logging.info('Following AMIs are going to be deregistered:')
            for i in old_amis:
                logging.info('[%s][%s][%s]' % (i['Name'], i['ImageId'], i['CreationDate']))
            if deregister_amis(amis=old_amis):
                logging.info('Deregister old AMIs succeed')
            else:
                logging.info('Something wrong when deregistering old AMIs')
        else:
            logging.info('No AMI is going to be deregistered:')
    return

## Search amis
def lookup_amis(LookupPattern):
    sts = boto3.client('sts')
    caller = sts.get_caller_identity()
    account_arn = caller['Arn']
    account_id = caller['Account']

    ## verify again, don't be fool
    if len(LookupPattern) > 15 and LookupPattern.count('*') <= 1 and LookupPattern.strip():
        LookupPattern = LookupPattern.strip()
    else:
        return

    logging.info('Account ID running: %s' % account_arn)
    ec2 = boto3.client('ec2')
    images = ec2.describe_images(
        Owners = [account_id],
        Filters = [{
            'Name': 'name',
            'Values': [LookupPattern]
        }]
    )
    return sorted(images['Images'], key=itemgetter('CreationDate'))

def deregister_amis(amis):
    if not amis:
        logging.info('This function should not be called when ami list is empty!')
        return False
    ec2 = boto3.client('ec2')
    for i in amis:
        try:
            # uncomment below line to perform real AMI removal
            #ec2.deregister_image(ImageId=i['ImageId'])
            logging.info('Deregistering AMI succeed: %s' % i['ImageId'])
        except Exception as e:
            logging.info('Error when deregistering ami: %s' % i['ImageId'])
            logging.info(str(e))
            return False
    return True


