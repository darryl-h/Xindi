# Xindi
This is a media center cluster. It contains 6 solutions: 
* Organizr to manage all the portals
* Sonaar for management of TV shows
* Radarr for management of movies
* nzbget to download newsgroups
* Deluge to download torrents, Jackett to manage Torrent indexes, and openVPN for safe torrent downloading
* Plex Server for media playback

It was named after the Star Trek Xindi race which were were six sentient species who evolved on the same planet in the Delphic Expanse 

# Setup
1. Create a directory for media, in my case, I use `/docker/data/` (Or change the locations in the docker-compose.yml file)
    1. Create the directories  
       `mkdir --parents /docker/data/media/movies`  
       `mkdir /docker/data/download`  
       `mkdir /docker/data/media/series`  
    1. Change ownership on the directory to the user that will run the container  
       `chown --recursive <user:group> /docker/data`
1. Create a directory for the cluster (This is optional, it will be created in the following step anyway)
    1. `mkdir ~/xindi`
1. Create a configuration directory for each the containers (Or change the locations in the docker-compose.yml file)  
    1. `mkdir --parents ~/xindi/organizr/config/`
    1. `mkdir --parents ~/xindi/deluge/config/`
    1. `mkdir --parents ~/xindi/jackett/config/`
    1. `mkdir --parents ~/xindi/nzbget/config`
    1. copy the `nzbget.conf` from here into `~/xindi/nzbget/config`
    1. Modify the `nzbget.conf` as needed (nzbget and news configurations)
    1. `mkdir --parents ~/xindi/plex/config`
    1. `mkdir --parents ~/xindi/radarr/config`
    1. `mkdir --parents ~/xindi/sonarr/config`
1. Copy the `docker-compose.yml` from this repository to the `~/xindi` directory
1. Make any other changes you desire in the `docker-compose.yml`
1. Start the cluster
    1. `docker compose up`
1. Add the following portals to Organizr
    1. Sonarr is on port 8989
    1. Radarr is on port 7878
    1. NZBGet is on port 6789
    1. Plex is on port 32400/web
    1. Deluge is on port 8112
    1. Jackett is on port 9117

# Setup on QNAP NAS with Container Station

## Updating Containers
To update the containers, click on Edit -> Recreate -> put a check in 'Try pulling the image from the registry before creating the container' and then next -> next -> finish


### Basic Containers:
#### Samba Server
* Image: crazymax/samba
* Network:
  * Network Mode: `Bridge`
  * Interface: `Adapter 2- Virtual Switch`
* Environment:
  * PGID=`911`
  * PUID=`911`
  * SAMBA_SHARES=`movies:/mnt/movies:no:no:yes,downloads:/mnt/downloads:no:no:yes,tv:/mnt/tv:no:no:yes`
  * SAMBA_USERS=`SomeUser:MySecretPassword`
* Storage:
  * Volume: config_samba:`/data`
  * Volume: downloads:`/mnt/downloads`
  * Volume: Movies:`/mnt/movies`
  * Volume: TVShows:`/mnt/tv`

#### Organizr
* Image: organizr/organizr:latest 
* Network:
  * Network Mode: `Default: NAT`
  * Ports: 80:80/tcp # Move the NAS to some other port before you do this!
  * Ports: 443 # unmap this, we don't need it.
* Storage:
  * Volume: config_organizr:`/config`

#### Plex
* Image: linuxserver/plex:latest 
* Network:
  * Network Mode: `Host`
* Storage:
  * Volume: config_plex:`/config`
  * Volume: Movies:`/movies`
  * Volume: TVShows:`/tvshows`

#### Sonarr
* Image: linuxserver/sonarr:latest
* Network:
  * Network Mode: `Host` # This is to get around hairpinning to the indexers/download clients
* Storage:
  * Volume: config_sonarr:`/config`
  * Volume: downloads:`/downloads`
  * Volume: TVShows:`/tvshows`

#### Radarr
* Image: linuxserver/radarr:latest
* Network:
  * Network Mode: `Host` # This is to get around hairpinning to the indexers/download clients
* Storage:
  * Volume: config_plex:`/config`
  * Volume: downloads:`/downloads`
  * Volume: Movies:`/movies`

#### Jackett
* Image: linuxserver/jackett:latest
* Network:
  * Network Mode: `Default: NAT`
  * Ports: 9117:9117/tcp
* Environment:
* Storage:
  * Volume: config_jackett:`/config`
 
#### NZBGet
* Image: linuxserver/nzbget:latest
* Network:
  * Network Mode: `Default: NAT`
  * Ports: 6789:6789/tcp
* Environment:
* Storage:
  * Volume: config_nzbget:`/config`
  * Volume: downloads:`/downloads`

### Applications
* Networking
  * By default, Container Station does not support using another containers network, to get around that, we will use the `Applications` feature in Container Station which allows us to use a docker compose YAML directly.
  * Container Station does not appear to allow different `Applications` to refer to another `Applications`'s container via the container name (IE: `network_mode: container:gluetun` doesn't seem to work, and the child container seems to have no networking)
  * Based on this, we will need to house both the VPN container (glutun), and the child container (the torrent container) in the same `Applications`.

* Using "File Station" we will create the configuration data for these two containers so they don't accidently get pruned by the user, becuase Container Station is not smart enough to enumerate these for some reason.
  * The download volumes are mapped wierd (`/share/CACHEDEV1_DATA/Container/container-station-data/lib/docker/volumes/`), b/c we are sharing the download volumes with some of the other basic containers that we are managing fully from Container Station.
  * In `DataVol1/Container` create a new directory called `config_data`
  * In `DataVol1/Container/config_data` create a new directory called `glutun`
  * In `DataVol1/Container/config_data` create a new directory called `transmission`

* Transmission
I've created the `manage_transmission.py` script above which is meant to be run from a seperate system and manage torrents within Transmission. It will give the torrent some time to normalize, remove stalled/slow (configurable) torrents, and completed torrents. These are configurable within the script. If you want to use my defaults, you just need to change the TRANSMISSION_HOST value within the script, then set it up on a cron (IE: I run it every 5 minutes with something like this: `*/5 * * * * cd /path/to/script && ./manage_transmission.py`

```bash
# Transmission RPC settings
TRANSMISSION_HOST = "TRANSMISSION_IP"
TRANSMISSION_PORT = 9091
# If authentication is required, set these:
TRANSMISSION_USER = ""
TRANSMISSION_PASS = ""

# Time (in minutes) to wait after torrent is added before checking its stats (for downloading torrents)
STABILIZATION_DELAY = 15

# For torrents still downloading: if download rate < MIN_DOWNLOAD_RATE (in KB/s)
# for at least MIN_RATE_DURATION minutes, remove torrent.
MIN_DOWNLOAD_RATE = 25      # in KB/s
MIN_RATE_DURATION = 30      # minutes

# For completed torrents: remove the torrent (but not the data) if complete for more than:
POST_COMPLETION_DELAY = 30  # minutes
```

* gluetun VPN Container:
  * There are some issues trying to use the linuxserver.io https://www.linuxserver.io/  wireguard continaer (https://docs.linuxserver.io/images/docker-wireguard/) working with QNAP (iptables) which I wasn't able to resolve in a meaningful amount of time, so I found and used the gluetun container instead, which supports BOTH VPN and Wireguard. (Pretty slick!)
  * For Private Internet Access, they do not provide a wireguard configuration, so you will need to create the configs yourself if you want to use WireGuard, OR use OpenVPN
    * triffid's - last update in 2024 - [https://github.com/triffid/pia-wg/tree/master](https://github.com/triffid/pia-wg/tree/master)
    * kchiem's - last update in 2024 - [https://github.com/kchiem/pia-wg](https://github.com/kchiem/pia-wg)
    * hsand's - last update in 2022 - [https://github.com/hsand/pia-wg](https://github.com/hsand/pia-wg)

```yaml
services:
  glutun_svc:
    image: qmcgaw/gluetun
    container_name: gluetun
    cap_add:
      - NET_ADMIN
    devices:
      - /dev/net/tun:/dev/net/tun
    ports:
      - 8888:8888/tcp # HTTP proxy
      - 8388:8388/tcp # Shadowsocks
      - 8388:8388/udp # Shadowsocks
      - 9091:9091/tcp # Transmission WebUI Port
    volumes:
      - /share/CACHEDEV1_DATA/Container/config_data/glutun/_data:/gluetun
    environment:
      - PUID=911
      - PGID=911
      # See https://github.com/qdm12/gluetun-wiki/tree/main/setup#setup
      - VPN_SERVICE_PROVIDER=private internet access
      - VPN_TYPE=openvpn
      # OpenVPN:
      - OPENVPN_USER=MY_PIA_USERNAME
      - OPENVPN_PASSWORD=MY_PIA_PASSWORD
      - SERVER_HOSTNAMES=ca-toronto.privacy.network
      - PORT_FORWARD_ONLY=true
      - VPN_PORT_FORWARDING=on
      # Wireguard:
      # - WIREGUARD_PRIVATE_KEY=wOEI9rqqbDwnN8/Bpp22sVz48T71vJ4fYmFWujulwUU=
      # - WIREGUARD_ADDRESSES=10.64.222.21/32
      # Timezone for accurate log times
      # Server list updater
      # See https://github.com/qdm12/gluetun-wiki/blob/main/setup/servers.md#update-the-vpn-servers-list
      - UPDATER_PERIOD=24h
      
  transmission_svc:
    image: lscr.io/linuxserver/transmission:latest
    container_name: transmission
    network_mode: service:glutun_svc
    environment:
      - PUID=911
      - PGID=911
    volumes:
      - /share/CACHEDEV1_DATA/Container/config_data/transmission/_data:/config
      - /share/CACHEDEV1_DATA/Container/container-station-data/lib/docker/volumes/downloads/_data:/downloads
    restart: unless-stopped
```

## tdarr:
One could install the server on the server, and then have the client running on the nodes, which is probably the right way to do it.
Installation:
https://docs.tdarr.io/docs/installation/windows-linux-macos

High Level overview:
1) Run the node
2) Run the server
3) Navigate to the server webUI (http://localhost:8265)
4) Click on the "Libraries" tab (https://youtu.be/KfEc0zy3oGU?si=XaZCdQxlyNTKkRuP&t=261)
5) Add libraries
6) Consider turning on 'folder watch'
7) Add the transcache folder
8) Click on "Transcode Options"
9) Move up "Migz Transcode Using Nvidia GPU & FFMPEG" above "Migz Transcode Using CPU & FFMPEG" and enable it
10) Consider disabling "Migz Transcode Using CPU & FFMPEG"
11) Consider changing the resolution of the videos -- https://www.reddit.com/r/Tdarr/comments/ifvn36/change_resolution/
12) Click on "Options" then "Scan (Fresh)" or "Scan (Find New)"
13) Wait for a LONG TIME.

Video tutorial below for step by step instructions:
https://www.youtube.com/watch?v=KfEc0zy3oGU


