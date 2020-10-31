#!/usr/bin/env python3

import argparse
import requests

def main(args, resolution):
    for user_url in args:
        id = user_url.split("/")[-1]
        # print(id)
        archive_url = "http://www.rtvs.sk/json/archive5f.json?id={i}".format(i=id)
        r = requests.get(archive_url)
        archive_d = r.json()
        # print("Archive JSON: {j}".format(j=archive_d))
        title = archive_d["clip"]["title"]
        mediaid = archive_d["clip"]["mediaid"]
        print("Title: {t} mediaid: {b}".format(
            t=title, b=mediaid))
        for source in archive_d["clip"]["sources"]:
            if source["type"] == 'application/x-mpegurl':
                m3u_url = source["src"]
        m3u_url = m3u_url.replace("/e8.", "/e1.")  # FIXME e7 times out
        main_url = "/".join(m3u_url.split("/")[0:3])
        # print("Getting m3u {m}".format(m=m3u_url))
        r = requests.get(m3u_url)
        r.encoding = 'utf-8'
        get_this_mp4 = False
        for m3u_line in r.iter_lines(decode_unicode=True):
            m3u_line = m3u_line.strip()
            # print("M3U line: {l}".format(l=m3u_line))
            if m3u_line.startswith("#EXT-X-STREAM-INF:"):
                for item in m3u_line.split(","):
                    key, value = item.split("=")
                    if key=="RESOLUTION":
                        print("Available resolution: {r}".format(
                            r=value))
                        if value == resolution:
                            # print("..which is our requested resolution")
                            get_this_mp4 = True
            if m3u_line.startswith("/") and get_this_mp4:
                chunks_url = "{u}{l}".format(
                    u=main_url, l=m3u_line)
                download_chunks(chunks_url, title, mediaid)
                get_this_mp4 = False

def download_chunks(chunklist_url, title, mediaid):
    mp4_url = "/".join(chunklist_url.split("/")[:-1]) # strip after last /
    print("Downloading chunks from url: {u}".format(u=mp4_url))
    r = requests.get(chunklist_url)
    r.encoding = 'utf-8'
    video_filename = "{t}_{b}.ts".format(
            t=title, b=mediaid)
    with open(video_filename, "wb") as video_fd:
        for line in r.iter_lines(decode_unicode=True):
            if line.startswith("#"):
                continue
            line = line.strip()
            # print(line)
            url = "{m}/{s}".format(
                m=mp4_url, s=line)
            print(".", end="", flush=True)
            r = requests.get(url, stream=True)
            for chunk in r.iter_content(chunk_size=1024*1024):
                # print("writing a chunk")
                video_fd.write(chunk)
    print()
    print("Saved to {f}".format(f=video_filename))
                    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--resolution', help="Resolution to download", default="1920x1080")
    parser.add_argument('url', nargs='*')
    args = parser.parse_args()
    main(args.url, args.resolution)
    
