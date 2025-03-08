import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# URLs
M3U_SOURCE_URL = "https://www.apsattv.com/localnow.m3u"
EPG_SOURCE_URL = "https://localnow.com/channels/epg-local-now-philadelphia"

# Output Files
M3U_OUTPUT_FILE = "localnow.m3u"
EPG_OUTPUT_FILE = "localnow.xml"

def fetch_m3u_channels():
    """Fetches and parses the M3U file to extract channel info."""
    response = requests.get(M3U_SOURCE_URL)
    if response.status_code != 200:
        print("❌ Failed to fetch M3U file")
        return []

    lines = response.text.split("\n")
    channels = []
    for i in range(len(lines)):
        if lines[i].startswith("#EXTINF"):
            channel_info = lines[i].split(",")[-1].strip()
            stream_url = lines[i+1].strip() if i+1 < len(lines) else ""
            channels.append({"name": channel_info, "url": stream_url, "id": channel_info.lower().replace(" ", "_")})
    
    return channels

def fetch_epg_data():
    """Scrapes EPG data from Local Now's website."""
    response = requests.get(EPG_SOURCE_URL)
    if response.status_code != 200:
        print("❌ Failed to fetch EPG data")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    programs = []

    for item in soup.find_all("div", class_="program"):
        title = item.find("h3").text if item.find("h3") else "Unknown"
        start_time = item.find("time", class_="start-time")
        start_time = start_time["datetime"] if start_time else None
        duration = int(item["data-duration"]) if "data-duration" in item.attrs else 30

        if start_time:
            start_datetime = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S.%fZ")
            end_datetime = start_datetime + timedelta(minutes=duration)
            programs.append({
                "title": title,
                "start": start_datetime.strftime("%Y%m%d%H%M%S") + " +0000",
                "end": end_datetime.strftime("%Y%m%d%H%M%S") + " +0000"
            })

    return programs

def generate_m3u(channels):
    """Creates a new M3U file with EPG links included."""
    with open(M3U_OUTPUT_FILE, "w", encoding="utf-8") as file:
        file.write("#EXTM3U\n")
        for channel in channels:
            file.write(f'#EXTINF:-1 tvg-id="{channel["id"]}" tvg-name="{channel["name"]}" tvg-logo="" group-title="Local Now", {channel["name"]}\n')
            file.write(f"{channel['url']}\n")
    print(f"✅ M3U file saved as {M3U_OUTPUT_FILE}")

def generate_epg(channels, programs):
    """Generates an XMLTV EPG file."""
    tv = ET.Element("tv")

    for channel in channels:
        channel_elem = ET.SubElement(tv, "channel", id=channel["id"])
        ET.SubElement(channel_elem, "display-name").text = channel["name"]

    for program in programs:
        prog_elem = ET.SubElement(tv, "programme", start=program["start"], stop=program["end"], channel=channels[0]["id"])
        ET.SubElement(prog_elem, "title").text = program["title"]

    tree = ET.ElementTree(tv)
    tree.write(EPG_OUTPUT_FILE, encoding="utf-8", xml_declaration=True)
    print(f"✅ EPG file saved as {EPG_OUTPUT_FILE}")

if __name__ == "__main__":
    print("📡 Fetching M3U channels...")
    channels = fetch_m3u_channels()
    if not channels:
        print("⚠️ No channels found. Exiting.")
    else:
        print("📺 Fetching EPG data...")
        programs = fetch_epg_data()
        if not programs:
            print("⚠️ No EPG data found. Exiting.")
        else:
            generate_m3u(channels)
            generate_epg(channels, programs)
            print("🎉 Local Now IPTV setup complete!")
