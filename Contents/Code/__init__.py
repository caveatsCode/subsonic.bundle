
NAME           = "subsonic"
PREFIX         = "/music/subsonic"
CACHE_INTERVAL = 10
ART            = "art-default.png"
ICON           = "icon-default.png"
BASE_URL       = "http://192.168.0.100:10101/"
ARTIST         = "{http://subsonic.org/restapi}artist"
ALBUM          = "{http://subsonic.org/restapi}album"
SONG           = "{http://subsonic.org/restapi}song"

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
  dir = ObjectContainer(title1="Artists")
  element = XML.ElementFromURL(makeURL("getArtists.view", v="1.9.0", c="plex"), cacheTime=CACHE_INTERVAL)
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
  element = XML.ElementFromURL(makeURL("getArtist.view", v="1.9.0", c="plex", id=artistID), cacheTime=CACHE_INTERVAL)
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
  element = XML.ElementFromURL(makeURL("getAlbum.view", v="1.9.0", c="plex", id=albumID), cacheTime=CACHE_INTERVAL)
  albumName = element.find(ALBUM).get("name")
  dir = ObjectContainer(title1=albumName)
  for item in searchElementTree(element, SONG):
    title       = item.get("title")
    id          = item.get("id")
    rating_key  = id
    duration = 1000 * int(item.get("duration"))
    url = makeURL("stream.view", v="1.9.0", c="plex", id=id, format="mp3")
    dir.add(TrackObject(title=title, duration=duration, key=url, rating_key=rating_key))
  return dir
    
#try to return thumbnail, else use default
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