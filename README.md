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

# Setup on QNAP NAS:
## tdarr:
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
11) Click on "Options" then "Scan (Fresh)" or "Scan (Find New)"
12) Wait for a LONG TIME.

Video tutorial below for step by step instructions:
https://www.youtube.com/watch?v=KfEc0zy3oGU


