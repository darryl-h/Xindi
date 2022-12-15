# Xindi
This is a media center cluster. It contains 6 solutions: Management of TV (sonaar) and Movie (radarr) shows, Newsgroup (nzbget) & Torrent downloader (deluge/jackett), Media compression (Tdarr) and playback (Plex). It was named after the Star Trek Xindi race which were were six sentient species who evolved on the same planet in the Delphic Expanse 

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
    1. `mkdir --parents ~/xindi/deluge/config/`
    1. `mkdir --parents ~/xindi/jackett/config/`
    1. `mkdir --parents ~/xindi/nzbget/config`
    1. `mkdir --parents ~/xindi/plex/config`
    1. `mkdir --parents ~/xindi/radarr/config`
    1. `mkdir --parents ~/xindi/sonarr/config`
    1. `mkdir --parents ~/xindi/tdarr/config`
    1. `mkdir ~/xindi/tdarr/server`
    1. `mkdir ~/xindi/tdarr/logs`
    1. `mkdir ~/xindi/tdarr/transcode_cache` in the `docker-compose.yml`
1. Copy the `docker-compose.yml` from this repository to the `~/xindi` directory
1. Configure the nzbget username and password
    1. `- NZBGET_USER=USERNAME #optional`
    1. `- NZBGET_PASS=PASSWORD #optional`
1. Configure the deluge PIA username and password in the `docker-compose.yml`
    1. `- OPENVPN_USERNAME=user`
    1. `- OPENVPN_PASSWORD=pass`
1. Make any other changes you desire in the `docker-compose.yml`
1. Start the cluster
    1. `docker compose up`
1. Configure each portal as needed
    1. Sonarr is on port 8989
    1. Radarr is on port 7878
    1. NZBGet is on port 6789
    1. Tdarr is on port 8265
    1. Plex is on port 32400/web
    1. Deluge is on port 8112
    1. Jackett is on port 9117
