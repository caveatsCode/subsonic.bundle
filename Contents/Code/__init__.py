
NAME                    = "subsonic"
PREFIX                  = "/music/subsonic"
CACHE_INTERVAL          = 10
ART                     = "art-default.png"
ICON                    = "icon-default.png"
ARTIST                  = "{http://subsonic.org/restapi}artist"
ALBUM                   = "{http://subsonic.org/restapi}album"
SONG                    = "{http://subsonic.org/restapi}song"
SUBSONIC_API_VERSION    = "1.9.0"
SUBSONIC_CLIENT         = "plex"

import binascii

####################################################################################################

@handler(PREFIX, NAME)
def main():
  dir = ObjectContainer(title1="Subsonic")
  dir.add(DirectoryObject(title="Artists", key = PREFIX + '/getArtists'))
  #add preferences option
  dir.add(PrefsObject(title="Preferences"))
  return dir

#create a menu listing all artists
@route(PREFIX + '/getArtists')
def getArtists():
  if not serverStatus():
    return ObjectContainer(header="Can't Connect", message="Check that your username, password and server address are entered correctly.")
  dir = ObjectContainer(title1="Artists")
  element = XML.ElementFromURL(makeURL("getArtists.view"), cacheTime=CACHE_INTERVAL)
  #add all artists
  for item in searchElementTree(element, ARTIST):
    title       = item.get("name")
    id          = item.get("id")
    key        = PREFIX + '/getArtist/' + id
    rating_key  = id
    dir.add(ArtistObject(title=title, key=key, rating_key=rating_key))
  return dir
  
#create a menu with all albums for selected artist
@route(PREFIX + '/getArtist/{artistID}')
def getArtist(artistID):
  element = XML.ElementFromURL(makeURL("getArtist.view", id=artistID), cacheTime=CACHE_INTERVAL)
  artistName = element.find(ARTIST).get("name")
  dir = ObjectContainer(title1=artistName)
  for item in searchElementTree(element, ALBUM):
    title       = item.get("name")
    id          = item.get("id")
    key        = PREFIX + '/getAlbum/' + id
    rating_key  = id
    dir.add(AlbumObject(title=title, key=key, rating_key=rating_key))
  return dir
  
#create a menu with all songs for selected album
@route(PREFIX + '/getAlbum/{albumID}')
def getAlbum(albumID):
  #set audio format based on prefs
  container = Prefs['format']
  if container == 'mp3':
    audio_codec = AudioCodec.MP3
  elif container == 'aac':
    audio_codec = AudioCodec.AAC
  
  #populate the track listing
  element = XML.ElementFromURL(makeURL("getAlbum.view", id=albumID), cacheTime=CACHE_INTERVAL)
  albumName = element.find(ALBUM).get("name")
  dir = ObjectContainer(title1=albumName)
  for item in searchElementTree(element, SONG):
    title       = item.get("title")
    id          = item.get("id")
    rating_key  = id
    duration = 1000 * int(item.get("duration"))
    url = makeURL("stream.view", id=id, format=container)
    dir.add(TrackObject(
      title=title, 
      duration=duration, 
      key=url, #might need to change this line eventually to return metadata instead of playing track
      rating_key=rating_key,
      items = [
        MediaObject(
          parts = [
            PartObject(key=Callback(playAudio, url=url, ext=container))
          ],
          container = container,
          audio_codec = audio_codec,
          audio_channels = 2,
          platforms=[]
        )
      ]))
  return dir
  
#play an audio track (copied this function from the Plex Shoutcast channel)
def playAudio(url):
	content = HTTP.Request(url, cacheTime=0).content
	if content:
		return content
	else:
		raise Ex.MediaNotAvailable
    
#try to return thumbnail, else use default (currently unused)
def Thumb(url):
  try:
    data       = HTTP.Request(url, cacheTime=CACHE_1WEEK).content
    return DataObject(data, 'image/jpeg')
  except:
    return Redirect(R(ICON))
    
#construct a http GET request from a view name and parameters
def makeURL(view, **parameters):
  url = Prefs['server']
  url += "rest/" + view + "?"
  parameters['u'] = Prefs['username']
  parameters['p'] = "enc:" + binascii.hexlify(Prefs['password'])
  parameters['v'] = SUBSONIC_API_VERSION
  parameters['c'] = SUBSONIC_CLIENT
  for param in parameters:
    url += param + "=" + parameters[param] + "&"
  return url

#recursively search etree and return list with all the elements that match  
def searchElementTree(element, search):
  matches = element.findall(search)
  if len(element):
    for e in list(element):
      matches += searchElementTree(e, search)
  return matches

#check that media server is accessible
def serverStatus():
  #check that Preferences have been set
  if not (Prefs['username'] and Prefs['password'] and Prefs['server']):
    return False
  #try to ping server with credentials
  elif XML.ElementFromURL(makeURL("ping.view"), cacheTime=CACHE_INTERVAL).get("status") != "ok":
    return False
  #connection is successful, return True and proceed!
  else:
    return True
    
#Plex calls this functions anytime Prefs are changed
def ValidatePrefs():
  if Prefs['server'][-1] != '/':
    return ObjectContainer(header="Check Server Address", message="Server address must end with a slash character ie http://127.0.0.1:8080/")
  elif not serverStatus():
    return ObjectContainer(header="Can't Connect", message="Check that your username, password and server address are entered correctly.")