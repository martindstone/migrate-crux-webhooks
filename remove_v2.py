#!/usr/bin/env python

import pd
import csv
import json
import os

app_base_url = os.environ.get('APP_BASE_URL', 'https://event-sender.herokuapp.com')
with open('domains.csv') as csvfile:
    readCSV = csv.DictReader(csvfile)
    domains_processed = set()
    for row in readCSV:
        if row['domain'] in domains_processed:
            print(f"-- Already processed {row['domain']}\n")
            continue
        try:
            extensions = pd.fetch(token=row['token'], endpoint="extensions")
            subs = pd.get_subs(row['token'])
        except:
            print(f"-- Oops, couldn't get extensions for {row['domain']}\n")
            continue
        domains_processed.add(row['domain'])
        print(f"Processing domain {row['domain']}")
        webhook_v2_extensions = [extension for extension in extensions if extension['extension_schema']['id'] == 'PJFWPEP']
        crux_extensions = [extension for extension in webhook_v2_extensions if extension['endpoint_url'] == f"{app_base_url}/respond"]
        v2_by_service = {}
        for extension in crux_extensions:
            if len(extension['extension_objects']) > 1:
                print(f"== Extension {extension['id']} has {len(extension['extension_objects'])} objects?!")
            for extension_object in extension['extension_objects']:
                if not extension_object['id'] in v2_by_service:
                    v2_by_service[extension_object['id']] = []
                v2_by_service[extension_object['id']].append(extension)

        v3_subs = [sub for sub in subs if 'delivery_method' in sub and 'url' in sub['delivery_method'] and sub['delivery_method']['url'] == f"{app_base_url}/respond"]
        v3_by_service = {}
        for sub in v3_subs:
            if not sub['filter']['id'] in v3_by_service:
                v3_by_service[sub['filter']['id']] = []
            v3_by_service[sub['filter']['id']].append(sub)
        
        print(f"  Services with v2 webhooks: {', '.join(v2_by_service.keys())}")
        print(f"  Services with v3 webhooks: {', '.join(v3_by_service.keys())}")

        v2_set = set(v2_by_service.keys())
        v3_set = set(v3_by_service.keys())
        both_set = v2_set.intersection(v3_set)
        v2_only_set = v2_set - v3_set
        v3_only_set = v3_set - v2_set
        print(f"  Services with both v2 and v3 webhooks: {', '.join(both_set)}")
        print(f"  Services with only v2 webhooks: {', '.join(v2_only_set)}")
        print(f"  Services with only v3 webhooks: {', '.join(v3_only_set)}")

        for service_id in v2_only_set:
            for extension in v2_by_service[service_id]:
                print(f"  Remove v2 webhook {extension['id']}")
                # pd.remove_webhook(row['token'], extension['id'])
        print('')