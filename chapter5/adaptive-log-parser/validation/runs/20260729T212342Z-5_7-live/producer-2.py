import datetime, time
events=[('inventory_lookup',34,'ok','stock check completed'),('payment_api',181,'retry','upstream requested retry'),('payment_api',412,'timeout','deadline exceeded')]
for tool,latency,status,message in events:
    started=time.perf_counter(); time.sleep(0.003); observed=max(latency,int((time.perf_counter()-started)*1000))
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='milliseconds')
    level='ERROR' if status=='timeout' else ('WARNING' if status=='retry' else 'INFO')
    print(f'[{stamp}] ({level}) <tool={tool}> {{latency_ms={observed} status={status}}} :: {message}', flush=True)
