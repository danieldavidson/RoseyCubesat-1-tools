import argparse
import logging
import os
import shlex
import subprocess
from datetime import datetime, timedelta

from dateutil import parser as dateparser

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--source_file", "-f", required=True, action="store")
    args = argparser.parse_args()

    if not os.path.exists(args.source_file):
        raise ValueError("Source file does not exist.")

    with open(args.source_file, "r") as f:
        f_lines = f.read().split("\n")

    ordered_date_list = []
    date_dict = {}
    for line in f_lines:
        line_parts = line.split("|")
        if len(line_parts) == 2:
            date = line_parts[0]
            date_bucket = date[:16]  # trim off seconds
            if date_bucket not in date_dict:
                ordered_date_list.append(date_bucket)
                date_dict[date_bucket] = 0
            date_dict[date_bucket] += 1

    date_queue = []
    count_accum: int = 0
    earliest_date: datetime | None = None
    for date_bucket in ordered_date_list:
        date_bucket_date = dateparser.parse(date_bucket)
        count = date_dict[date_bucket]
        if count <= 2:
            continue
        # case 1: start of bucket
        if not earliest_date:
            earliest_date = date_bucket_date
            date_queue.append(date_bucket)
            count_accum += count
        # case 2: middle of bucket
        elif dateparser.parse(
                date_queue[len(date_queue) - 1]
        ) - date_bucket_date <= timedelta(minutes=1):
            date_queue.append(date_bucket)
            count_accum += count
        # case 3: after bucket
        else:
            # case 3.1: legit image
            if count_accum >= 500:
                logging.info(f"{date_queue}\t{count_accum}")
                cmd_arg = f"python3 decode_imagery.py"
                cmd_arg += f" -f {args.source_file}"
                cmd_arg += f" -e \"{date_queue[0] + ':59'}\""
                cmd_arg += f" -s \"{date_queue[len(date_queue) - 1] + ':00'}\""
                cmd_arg += f" -p \"{date_queue[0].replace(' ', '-').replace(':', '') + '-'}\""
                subprocess.call(shlex.split(cmd_arg))
            # case 3.2: not legit image
            else:
                pass
            # clean up
            date_queue = []
            count_accum = 0
            earliest_date = None
