# https://apps.apple.com/us/charts/iphone/health-fitness-apps/6013?chart=top-free
#https://apps.apple.com/us/charts/iphone/health-fitness-apps/6013?chart=top-paid
# read category from config

# list all appleid url under this category

# run scrape of each apple id

import aiohttp
import os
import csv
import time
import asyncio
from aiohttp_socks import ProxyType, ProxyConnector, ChainProxyConnector
from DataRecorder import Recorder
import pandas as pd

# Constants
PROXY_URL = None
DOMAIN_LIST = [
  'https://apps.apple.com/us/charts/iphone', 'https://apps.apple.com/us/charts/ipad'
]

# File Paths
RESULT_FOLDER = "./result"
OUTPUT_FOLDER = "./output"

# Helper Functions
def process_line(csv_file, lines):
    """Process and save lines to CSV."""
    
    # Create file and write header if it doesn't exist
      
    for line in lines:
        try:
            line = line.strip()
            if ' ' in line:
                timestamp, original_url = line.split(' ')
                data = {'timestamp': timestamp, 'url': original_url}
                csv_file.add_data(data)
        except Exception as e:
            print(f"Failed to process line: {line}, Error: {e}")


async def get_urls_from_archive(domain, start, end):
    """Fetch URLs from the Wayback Machine."""
    subs_wildcard = "*."
    domainname = domain.replace("https://", "")
    domainname=domainname.replace('/','-')
    
    csv_filepath = f'{RESULT_FOLDER}/{domainname}.csv'
    csv_file=Recorder(csv_filepath)

    fieldnames = ['timestamp', 'url']
    if not os.path.exists(csv_filepath):
        csv_file.add_data(fieldnames)

    query_url = f"http://web.archive.org/cdx/search/cdx?url={subs_wildcard}{domain}/&fl=timestamp,original"
    filter = f"&statuscode=200&from={start}&to={end}" if end else f"&statuscode=200&from={start}"
    query_url += "&collapse=urlkey" + filter
    # query_url=query_url+'&matchType=prefix'
    query_url=query_url+f'&statuscode=200&from={current-1}'

  

    headers = {
        'Referer': 'https://web.archive.org/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
    }

    try:
        async with aiohttp.ClientSession(connector=None) as session:
            async with session.get(query_url, headers=headers, 
                                   proxy='http://127.0.0.1:1080',
                                   timeout=3000) as resp:
                if resp.status != 200:
                    print(f"Received status code {resp.status}.")
                    return

                count = 0
                buffer = bytearray()
                while True:
                    chunk = await resp.content.read(1024)
                    if not chunk:
                        if buffer:
                            process_line(csv_file, [buffer.decode('utf-8', 'replace')])
                        break
                    buffer.extend(chunk)
                    raw = buffer.decode('utf-8', 'replace')
                    lines = raw.splitlines(True)

                    for line in lines[:-1]:
                        process_line(csv_file, [line])
                    buffer = bytearray(lines[-1], 'utf-8')

                    count += len(lines)
                    print(f"Processed {count} lines so far...")

    except Exception as e:
        print(f"Error fetching data: {e}")
    csv_file.record()

async def fetch_urls_for_domain(domain, start, end):
    """Fetch URLs for a specific domain with retry logic."""
    retries = 5
    for attempt in range(retries):
        try:
            await get_urls_from_archive(domain, start, end)

            break  # Break if successful
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            print(f"Connection error on attempt {attempt + 1}: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(20 * attempt * (attempt + 1))  # Exponential backoff
            else:
                print("Max retries reached. Exiting.")
def extract_urls(domain):
    domainname = domain.replace("https://", "")
  
    domainname=domainname.replace('/','-')


    csv_file = f'{RESULT_FOLDER}/{domainname}.csv'
    if not os.path.exists(csv_file):
        print('{domain} category urls file not prepared yet')
        return
    df=pd.read_csv(csv_file)
    urls=df['url']
    urls=[x if x and 'top-' in x  else None for x in urls]
    urls=list(set(urls))
    print(urls)
    for t in ['paid','free']:
        urls=[x if x and '-'+t in x else None for x in urls]
    # freeurls=[x if x and  '-'+t in x else None for x in urls]
        out_filepath=f'{RESULT_FOLDER}/ipad-top-{t}.csv'

        if '/iphone/' in domain:
            out_filepath=f'{RESULT_FOLDER}/iphone-top-{t}.csv'
  
        out_file=Recorder(out_filepath)

        out_file.add_data(urls)
        out_file.record()

async def main():
    """Main entry point to handle asynchronous execution."""
    start_year = 2024
    end_year = 2024

    # Generate pairs of consecutive years
    year_pairs = [(start_year + i, start_year + i + 1) for i in range(end_year - start_year)] if start_year != end_year else [(start_year, None)]
    
    tasks = []
    for domain in DOMAIN_LIST:
        for pair in year_pairs:
            print(f"Adding domain {domain} to tasks")
            task = asyncio.create_task(fetch_urls_for_domain(domain, pair[0], pair[1]))
            tasks.append(task)

    await asyncio.gather(*tasks)
    print('post processing urls')
    for domain in DOMAIN_LIST:
        extract_urls(domain)

    print(f"Completed in {time.time() - start_time} seconds.")





if __name__ == "__main__":
    # Ensure result and output directories exist
    os.makedirs(RESULT_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    print("Directory setup complete.")
    start_time = time.time()

    # Run the main async task
    asyncio.run(main())


