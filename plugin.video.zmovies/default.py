'''
    Z-Movies (zmovie.tv) XBMC Plugin
    Copyright (C) 2013 XUNITYTALK.COM

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.		
'''

import os
import string
import sys
import re
import urlresolver
import xbmc, xbmcaddon, xbmcplugin, xbmcgui

from t0mm0.common.addon import Addon
from t0mm0.common.net import Net

from metahandler import metahandlers

addon_id = 'plugin.video.zmovies'

net = Net()
addon = Addon(addon_id, sys.argv)

#Common Cache
import xbmcvfs
dbg = False # Set to false if you don't want debugging

#Common Cache
try:
  import StorageServer
except:
  import storageserverdummy as StorageServer
cache = StorageServer.StorageServer('plugin.video.zmovies')
cache_rtmp = StorageServer.StorageServer('plugin.video.zmovies.rtmp', timeout=72)

################### Global Constants #################################

#URLS
BASEURL = 'http://zmovie.tv/'

def AddSysPath(path):
    if path not in sys.path:
        sys.path.append(path)

#PATHS
AddonPath = addon.get_path()
IconPath = os.path.join(AddonPath, 'icons')
LibsPath = os.path.join(AddonPath, 'resources', 'libs')
AddSysPath(LibsPath)

from universal import favorites, watchhistory
fav = favorites.Favorites(addon_id, sys.argv)

#VARIABLES
VideoType_Movies = 'movie'
VideoType_TV = 'tvshow'
VideoType_Season = 'season'
VideoType_Episode = 'episode'
VideoType_Link = 'link'

##### Queries ##########
play = addon.queries.get('play', '')
mode = addon.queries['mode']
url = addon.queries.get('url', '')
title = addon.queries.get('title', '')
img = addon.queries.get('img', '')
fanart = addon.queries.get('fanart', '')
section = addon.queries.get('section', '')
page = addon.queries.get('page', '')
video_type = addon.queries.get('video_type', '')
name = addon.queries.get('name', '')
imdb_id = addon.queries.get('imdb_id', '')
season = addon.queries.get('season', '')
episode = addon.queries.get('episode', '')
historytitle = addon.queries.get('historytitle', '')
historylink = addon.queries.get('historylink', '')
iswatchhistory = addon.queries.get('watchhistory', '')
year = addon.queries.get('year', '')
queued = addon.queries.get('queued', '')

#################### Addon Settings ##################################

#Helper function to convert strings to boolean values
def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")
  
meta_setting = str2bool(addon.get_setting('use-meta'))

metaget=metahandlers.MetaData()

#def WatchedCallback():
#    metaget=metahandlers.MetaData()
#    metaget.change_watched(video_type, title, imdb_id, season=season, episode=episode, year=year, watched=7)
#    xbmc.executebuiltin("Container.Refresh")
    
def WatchedCallbackwithParams(video_type, title, imdb_id, season, episode, year):
    metaget=metahandlers.MetaData()
    metaget.change_watched(video_type, title, imdb_id, season=season, episode=episode, year=year, watched=7)
    xbmc.executebuiltin("Container.Refresh")    
    
#################### Helper Functions ##################################

def escape(text):
        try:            
            rep = {" ": "%20"                  
                   }
            for s, r in rep.items():
                text = text.replace(s, r)

        except TypeError:
            pass

        return text
    
def unescape(text):
        try:            
            rep = {"&nbsp;": " ",
                   "\n": "",
                   "\t": "",                   
                   }
            for s, r in rep.items():
                text = text.replace(s, r)
				
            # remove html comments
            text = re.sub(r"<!--.+?-->", "", text)    
				
        except TypeError:
            pass

        return text

def Notify(typeq, title, message, times, line2='', line3=''):
     if title == '':
          title='Z-Movies'
     if typeq == 'small':
          if times == '':
               times='5000'
          smallicon= os.path.join(IconPath,'icon.png')
          xbmc.executebuiltin("XBMC.Notification("+title+","+message+","+times+","+smallicon+")")
     elif typeq == 'big':
          dialog = xbmcgui.Dialog()
          dialog.ok(' '+title+' ', ' '+message+' ', line2, line3)
     else:
          dialog = xbmcgui.Dialog()
          dialog.ok(' '+title+' ', ' '+message+' ')
		
def add_video_directory(mode, video_type, link, vidtitle, vidname, imdb='', year='', season_num=0, totalitems=0, favourite=False, img=''):

    meta = get_metadata(video_type, vidtitle, year=year, imdb=imdb, season_num=season_num, img=img)
    contextMenuItems = add_contextmenu(meta_setting, video_type, link, vidtitle, vidname, favourite, watched=meta['overlay'], imdb=meta['imdb_id'], year=year, season_num=season_num, img=img)

    meta['title'] = vidname
    addon.add_directory({'mode': mode, 'url': link, 'video_type': VideoType_Season, 'imdb_id': meta['imdb_id'], 'title': vidtitle, 'name': vidname, 'season': season_num, 'img': meta['cover_url'], 'fanart': meta['backdrop_url']}, meta, contextMenuItems, context_replace=True, img=meta['cover_url'], fanart=meta['backdrop_url'], total_items=totalitems)


def add_video_item(video_type, section, link, vidtitle, vidname, year='', imdb='', season_num=0, episode_num=0, totalitems=0, favourite=False, img=''):

    meta = get_metadata(video_type, vidtitle, vidname, year, imdb=imdb, season_num=season_num, episode_num=episode_num, img=img)
    if video_type == VideoType_Movies:
        contextMenuItems = add_contextmenu(meta_setting, video_type, link, vidtitle, meta['title'], favourite, watched=meta['overlay'], imdb=meta['imdb_id'], year=meta['year'], img=img)
    else:
        contextMenuItems = add_contextmenu(meta_setting, video_type, link, vidtitle, meta['title'], favourite, watched=meta['overlay'], imdb=meta['imdb_id'], season_num=season_num, episode_num=episode_num, img=img)
    
    if video_type == VideoType_Movies:
        infolabels = {'supports_meta' : 'true', 'video_type' : video_type, 'name' : vidtitle, 'imdb_id' : meta['imdb_id'], 'year' : meta['year']}
        queries = {'mode' : 'links', 'url': link, 'video_type': video_type, 'imdb_id': meta['imdb_id'], 'title': vidtitle, 'name': vidname, 'year':meta['year'], 'img': meta['cover_url'], 'fanart': meta['backdrop_url']}
        p_url = fav.build_url(queries)
        contextMenuItems.insert(1, ('Add to Favorites', fav.add_directory(vidtitle, p_url, section_title='Movies', img=meta['cover_url'], fanart=meta['backdrop_url'], infolabels=infolabels)))
        addon.add_directory(queries, meta, contextMenuItems, context_replace=True, img=meta['cover_url'], fanart=meta['backdrop_url'], total_items=totalitems)
    elif video_type == VideoType_Episode:
        addon.add_directory({'mode' : 'links', 'url': link, 'video_type': video_type, 'imdb_id': meta['imdb_id'], 'title': vidtitle, 'name': vidname, 'year':meta['year'], 'season': season_num, 'episode' : episode_num, 'img': meta['cover_url'], 'fanart': meta['backdrop_url']}, meta, contextMenuItems, context_replace=True, img=meta['cover_url'], fanart=meta['backdrop_url'], total_items=totalitems)

def add_video_link(video_type, link, vidtitle, vidname, img='', fanart='', totalitems=0):
    
    contextMenuItems = add_contextmenu(False, VideoType_Link, link, vidtitle, vidtitle, False)        
    
    queries = {'play' : 'true', 'url': link, 'video_type': video_type, 'title': vidtitle, 'name': vidname, 'year':year, 'img': img, 'fanart': fanart, 'historytitle' : vidtitle, 'historylink' : sys.argv[0]+sys.argv[2]}
    
    from universal import playbackengine    
    contextMenuItems.insert(0, ('Queue Item', playbackengine.QueueItem(addon_id, vidtitle, addon.build_plugin_url( queries ) ) ) )
    
    addon.add_directory(queries, {'title' : vidname}, contextMenuItems, context_replace=False, img=img, fanart=fanart, total_items=totalitems)
    
def setView(content, viewType):
    
    # set content type so library shows more views and info
    if content:
        xbmcplugin.setContent(int(sys.argv[1]), content)
    if addon.get_setting('auto-view') == 'true':
        xbmc.executebuiltin("Container.SetViewMode(%s)" % addon.get_setting(viewType) )
    
    # set sort methods - probably we don't need all of them
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_UNSORTED )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RATING )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_DATE )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_PROGRAM_COUNT )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_GENRE )  

#################### Favorites related functions ##################################
          
def Favorites(video_type):

    #Add Season/Episode sub folders
    if video_type == VideoType_TV:
        addon.add_directory({'mode': 'favorites', 'video_type': VideoType_Season}, {'title': '[COLOR blue]Seasons[/COLOR]'})
        addon.add_directory({'mode': 'favorites', 'video_type': VideoType_Episode}, {'title': '[COLOR blue]Episodes[/COLOR]'})

    #Grab saved favourites from DB and populate list
    saved_favs = cache.get('favorites_' + video_type)
    print '1'
    if saved_favs:
        print '2'
        favs = sorted(eval(saved_favs), key=lambda fav: fav[1])
        
        for fav in favs:
            print fav
            
            img=''
            if len(fav) == 7:
                img = fav[6]
                
            if video_type in (VideoType_Movies, VideoType_Episode):
                add_video_item(video_type, video_type, fav[5], fav[0].title(), fav[1].title(), imdb=fav[2], season_num=fav[3], episode_num=fav[4], totalitems=len(favs), favourite=True, img=img)
            elif video_type == VideoType_TV:
                add_video_directory('tvseasons', video_type, fav[5], fav[0].title(), fav[1].title(), imdb=fav[2], season_num=fav[3], totalitems=len(favs), favourite=True, img=img)
            elif video_type == VideoType_Season:
                add_video_directory('tvepisodes', video_type, fav[5], fav[0].title(), fav[1].title(), imdb=fav[2], season_num=fav[3], totalitems=len(favs), favourite=True, img=img)
    

def add_favorite():
    saved_favs = cache.get('favorites_' + video_type)
    favs = []
    
    if saved_favs:
        favs = eval(saved_favs)
        if favs:
            if (title, name, imdb_id, season, episode, url) in favs or (title, name, imdb_id, season, episode, url, img) in favs or (title, name, imdb_id, season, episode, url, None) in favs:
                Notify('small', 'Favorite Already Exists', name.title() + ' already exists in your Z-Movies favorites','')
                return

    favs.append((title, name, imdb_id, season, episode, url, img))
    cache.set('favorites_' + video_type, str(favs))
    Notify('small', 'Added to favorites', name.title() + ' added to your Z-Movies favorites','')


def remove_favorite():
    saved_favs = cache.get('favorites_' + video_type)
    if saved_favs:
        favs = eval(saved_favs)
        try:
            favs.remove((title, name, imdb_id, season, episode, url))
        except:
            pass
        try:
            favs.remove((title, name, imdb_id, season, episode, url, None))
        except:
            pass
        try:
            favs.remove((title, name, imdb_id, season, episode, url, img))
        except:
            pass
        cache.set('favorites_' + video_type, str(favs))
        xbmc.executebuiltin("XBMC.Container.Refresh")

        
#################### Meta-Data related functions ##################################

def refresh_movie(vidtitle, year=''):

    #metaget=metahandlers.MetaData()
    search_meta = metaget.search_movies(vidtitle)
    
    if search_meta:
        movie_list = []
        for movie in search_meta:
            movie_list.append(movie['title'] + ' (' + str(movie['year']) + ')')
        dialog = xbmcgui.Dialog()
        index = dialog.select('Choose', movie_list)
        
        if index > -1:
            new_imdb_id = search_meta[index]['imdb_id']
            new_tmdb_id = search_meta[index]['tmdb_id']       
            meta = metaget.update_meta('movie', vidtitle, imdb_id=imdb_id, new_imdb_id=new_imdb_id, new_tmdb_id=new_tmdb_id, year=year)   
            xbmc.executebuiltin("Container.Refresh")
    else:
        msg = ['No matches found']
        addon.show_ok_dialog(msg, 'Refresh Results')


def episode_refresh(vidname, imdb, season_num, episode_num):
    #refresh info for an episode   

    #metaget=metahandlers.MetaData()
    metaget.update_episode_meta(vidname, imdb, season_num, episode_num)
    xbmc.executebuiltin("XBMC.Container.Refresh")


def season_refresh(vidname, imdb, season_num):

    #metaget=metahandlers.MetaData()          	
    metaget.update_season(vidname, imdb, season_num)
    xbmc.executebuiltin("XBMC.Container.Refresh")

def get_metadata(video_type, vidtitle, vidname='', year='', imdb='', season_list=None, season_num=0, episode_num=0, img=''):
    
    if meta_setting:
        #Get Meta settings
        movie_poster = addon.get_setting('movie-poster')
        movie_fanart = addon.get_setting('movie-fanart')
        
        tv_banners = 'false' #addon.get_setting('tv-banners')
        tv_posters = 'false' #addon.get_setting('tv-posters')
        tv_fanart = 'false' #addon.get_setting('tv-fanart')                    
    
        if video_type in (VideoType_Movies, VideoType_TV):
            meta = metaget.get_meta(video_type, vidtitle, year=year)
    
        #Check for and blank out covers if option disabled
        if video_type==VideoType_Movies and movie_poster == 'false':
            meta['cover_url'] = img
        elif video_type==VideoType_TV and tv_banners == 'false':
            meta['cover_url'] = img
            
        #Check for banners vs posters setting    
        if video_type == VideoType_TV and tv_banners == 'true' and tv_posters == 'false':
            meta['cover_url'] = meta['banner_url']
        
        #Check for and blank out fanart if option disabled
        if video_type==VideoType_Movies and movie_fanart == 'false':
            meta['backdrop_url'] = ''
        elif video_type in (VideoType_TV, VideoType_Episode) and tv_fanart == 'false':
            meta['backdrop_url'] = ''

    else:
        meta = {}
        meta['title'] = vidname
        meta['cover_url'] = img
        meta['imdb_id'] = imdb
        meta['backdrop_url'] = ''
        meta['year'] = year
        meta['overlay'] = 0
        if video_type in (VideoType_TV, VideoType_Episode):
            meta['TVShowTitle'] = vidtitle

    return meta

    
#################### Context-Menu related functions ##################################

def add_contextmenu(use_meta, video_type, link, vidtitle, vidname, favourite, watched='', imdb='', year='', season_num=0, episode_num=0, img=''):
    
    contextMenuItems = []
    
    if video_type == VideoType_Link:
        return contextMenuItems
    
    contextMenuItems.append(('Show Information', 'XBMC.Action(Info)'))

    #Meta is turned on so enable extra context menu options
    if use_meta:
        if watched == 6:
            watched_mark = 'Mark as Watched'
        else:
            watched_mark = 'Mark as Unwatched'

        contextMenuItems.append((watched_mark, 'XBMC.RunPlugin(%s?mode=watch_mark&video_type=%s&title=%s&imdb_id=%s&season=%s&episode=%s)' % (sys.argv[0], video_type, vidtitle, imdb, season_num, episode_num)))
        contextMenuItems.append(('Refresh Metadata', 'XBMC.RunPlugin(%s?mode=refresh_meta&video_type=%s&title=%s&year=%s&season=%s&episode=%s)' % (sys.argv[0], video_type, vidtitle, year, season_num, episode_num)))
        
        #if video_type == VideoType_Movies:
            #contextMenuItems.append(('Search for trailer', 'XBMC.RunPlugin(%s?mode=trailer_search&vidname=%s&url=%s)' % (sys.argv[0], title, link)))                        

    return contextMenuItems
    

#################### Main Functions ##################################

def MainMenu(): 
    
    addon.add_directory({'mode' : 'browse', 'video_type': VideoType_Movies, 'section': 'movies'}, {'title':  'Movies'}, img=os.path.join(IconPath, 'movies.png'))
    addon.add_directory({'mode': 'resolver'}, {'title':  'Resolver Settings'})
    
    setView(None, 'default-view')

def Browse(section):
        
    addon.add_directory({'mode' : section, 'video_type': video_type, 'section': 'topfeatured'}, {'title':  '30 Top Featured'}, img=os.path.join(IconPath, '30topfeatured.png'))
    addon.add_directory({'mode' : section, 'video_type': video_type, 'section': 'new'}, {'title':  '30 New Releases'}, img=os.path.join(IconPath, '30newreleases.png'))
    addon.add_directory({'mode' : section, 'video_type': video_type, 'section': 'recent'}, {'title':  '30 New Additions'}, img=os.path.join(IconPath, '30newadditions.png'))
    addon.add_directory({'mode' : section, 'video_type': video_type, 'section': 'atoz'}, {'title':  'A-Z'})
    fav.add_my_fav_directory(img=os.path.join(IconPath, 'favorites.png'))
    addon.add_directory({'mode' : section, 'video_type': video_type, 'section': 'featured', 'page' : '1'}, {'title':  'Featured'}, img=os.path.join(IconPath, 'featured.png'))
    addon.add_directory({'mode' : section, 'video_type': video_type, 'section': 'genre'}, {'title':  'Genres'}, img=os.path.join(IconPath, 'genres.png'))
    addon.add_directory({'mode' : section, 'video_type': video_type, 'section': 'mostpopular'}, {'title':  'Most Popular'}, img=os.path.join(IconPath, 'mostpopular.png'))
    addon.add_directory({'mode' : section, 'video_type': video_type, 'section': 'search'}, {'title':  'Search'}, img=os.path.join(IconPath, 'search.png'))
    
    setView(None, 'default-view')
    
def GetTopFeatured():
                    
    url_content = net.http_GET(BASEURL).content
    
    item_contents = re.compile("<li id=\"mycarousel(.+?)</li>", re.DOTALL).findall(url_content)
    for item_content in item_contents:            
        item = re.search(r"<a.*?href=\"(.+?)\".+?<img.*?src=\"(.+?)\".+?alt=\"(.+?)\"", item_content)
        if item:
            item_url = item.group(1)
            item_title = item.group(3)
            item_img = item.group(2)
            
            year = re.search(r" \(([0-9]{4})\)$", item_title)
            if year:
                year = year.group(1)
                item_title = re.sub(r" \(([0-9]{4})\)$", "", item_title)
            else:
                year = ''
            
            add_video_item(video_type, video_type, item_url, item_title, item_title, year=year, totalitems=len(item_contents), img=item_img)                        
            
    setView('movies', 'movie-view')
    
def GetMostPopular(url):
        
    url_content = net.http_GET(url).content
    
    for mp in re.finditer(r"<a.+?href=\".+?/movies/top/(.+?)\".+?<b>(.+?)</b>", url_content):
        addon.add_directory({'mode' : 'section', 'video_type': video_type, 'url' : url + '/' + mp.group(1), 'page' : '1'}, {'title':  'Most Popular > ' + mp.group(2)})        
        
    setView(None, 'default-view')
    
def GetAtoZ():
        
    url_content = net.http_GET(BASEURL).content
    
    for mp in re.finditer(r"<a.+?href=\".+?/search/alpha/(.+?)\">(.+?)</a>", url_content):
        addon.add_directory({'mode' : 'section', 'video_type': video_type, 'url' : BASEURL + 'search/alpha/' + mp.group(1), 'page' : '1'}, {'title':  mp.group(2)})                
        
    setView(None, 'default-view')
    
def GetGenre():
        
    url_content = net.http_GET(BASEURL + 'search/genre').content
    
    for mp in re.finditer(r"<a.+?href=\".+?/search/genre/(.+?)\">(.+?)</a>", url_content):
        addon.add_directory({'mode' : 'section', 'video_type': video_type, 'url' : BASEURL + 'search/genre/' + mp.group(1), 'page' : '1'}, {'title':  mp.group(2)})                
        
    setView(None, 'default-view')

def Movies(section, page):
    if section == 'topfeatured':
        GetTopFeatured()
    elif section == 'mostpopular':
        GetMostPopular(BASEURL + 'movies/top')
    elif section == 'atoz':
        GetAtoZ()
    elif section == 'genre':
        GetGenre()
    elif section == 'search':
        ShowSearchDialog()
    else:
        section_url = BASEURL + 'movies/' + section
        GetSection(section_url, page)
    
def GetSection(url, page):
        
    page_url = url 
    if page:
        page_url = page_url + '/' + page
    url_content = net.http_GET(page_url).content
    
    page_content = re.search(r"(?s)<b>1.(.+?)</html>", url_content)
    if page_content:
        page_content = addon.unescape(page_content.group(1))
        page_content = unescape(page_content)
        
        item_contents = re.compile("<table.+?<tbody>.+?<div(.+?)</div>").findall(page_content)
        for item_content in item_contents:                    
            item = re.search(r"<a.+?</a>.*?<a.*?href=\"(.+?)\".+?title=\"(.+?)\".+?<img.*?src=\"(.+?)\"", item_content)
            if item:
                item_url = item.group(1)
                item_title = item.group(2)
                item_img = item.group(3)
                
                year = re.search(r" \(([0-9]{4})\)$", item_title)
                if year:
                    year = year.group(1)
                    item_title = re.sub(r" \(([0-9]{4})\)$", "", item_title)
                else:
                    year = ''
                
                add_video_item(video_type, video_type, item_url, item_title, item_title, year=year, totalitems=len(item_contents), img=item_img)                                        
                
        if page:
            next_page = re.search(r"Next+", url_content)
            if next_page:
                addon.add_directory({'mode' : 'section', 'video_type': video_type, 'url' : url, 'page' : str(int(page) + 1)}, {'title':  'Next Page >>'})        
                
    setView('movies', 'movie-view')
    
def IfResolverNotInURLResolverCheckHere(url):
    url = url.lower()
    mat = re.match('http://(?:www.)?(bdrip\.ws|skylo\.me|fleon\.me|hqvideo\.cc|streamme\.cc|worldvid\.co|vidgang\.co|hdvid\.ws|vidshare\.ws)/(?:(?:rc|vv|videos|playerframe)\.php\?id=|pc/|stream/|video/|play/)([0-9a-zA-Z]+)/?', url)
    if mat:
        return True
    return False

def IfResolverNotInURLResolverResolveHere(url):
    notify_title = title + ' - ' + name
    Notify('small', notify_title, 'Resolving...', '')
    
    url = url.lower()
    mat = re.match('http://(?:www.)?(bdrip\.ws|skylo\.me|fleon\.me|hqvideo\.cc|streamme\.cc|worldvid\.co|vidgang\.co|hdvid\.ws|vidshare\.ws)/(?:(?:rc|vv|videos|playerframe)\.php\?id=|pc/|stream/|video/|play/)([0-9a-zA-Z]+)/?', url)
    if not mat:
        return False    
    host = mat.group(1)
    id = mat.group(2)
    url = ''
    if host in ['bdrip.ws']:
        url = 'http://' + host + '/rc.php?Id=' + id
    elif host in ['skylo.me', 'fleon.me', 'hdvid.ws', 'vidshare.ws']:
        url = 'http://' + host + '/videos.php?Id=' + id
    elif host in ['hqvideo.cc', 'streamme.cc']:
        url = 'http://' + host + '/playerframe.php?Id=' + id
    elif host in ['worldvid.co', 'vidgang.co']:
        url = 'http://' + host + '/play/' + id + '/'
        
    print url
    
    Notify('small', notify_title, 'Searching for stream information file...', '15000')
    
    content = ''
    if host in ['worldvid.co', 'vidgang.co']:
        print net.http_GET(url.replace('/play/','/video/')).get_headers()
        content = net.http_POST(url, {'confirm':'Continue+as+Free+User'}).content
    else:
        content = net.http_GET(url).content
        
    content = addon.unescape(content)
    content = unescape(content)
    video = re.search(r"SWFObject\('(.+?)',.*?so.addVariable\('file','(.+?)'\)", content)
    swf = video.group(1)
    file = video.group(2)
    if file.endswith('.flv'):
        file = file.replace('.flv', '')
    elif file.endswith('.mp4'):
        file = 'mp4:' + file
   
    
    rtmp = ''
    rtmp = cache_rtmp.get(swf)
    sd=''
    if not rtmp:
        Notify('small', notify_title, 'Downloading stream information file...', '60000')
        ext_st = swf.rfind('.')
        ext = 'nana'
        if ext_st != -1:            
            ext = swf[ext_st:]
        
        import urllib2
        u = urllib2.urlopen(swf)
        
        content_blks = []
        block_sz = 12288
        while True:
            buffer = u.read(block_sz)
            if not buffer:
                break
            content_blks.append(buffer)
        u.close()       
        
        content = ''.join(content_blks)
        
        Notify('small', notify_title, 'Analysing stream information file... Please Wait...', '600000') 
        
        AddSysPath(os.path.join(LibsPath, 'swflib'))
        AddSysPath(os.path.join(LibsPath, 'zope.interface'))
        AddSysPath(os.path.join(LibsPath, 'zope.component'))
        AddSysPath(os.path.join(LibsPath, 'zope.event'))
        from fusion.swf import swfdump
        sd = swfdump.get_swfdump_from_bytestring(content, ext, "constants", "utf8")   
        rtmp = re.search(r"(rtmp\://.+?/.+?/)", sd)
        if rtmp:
            rtmp = rtmp.group(1)            
            cache_rtmp.set(swf, rtmp)        
        
    sd = None
    playable_url = ''
    if rtmp:
        Notify('small', notify_title, 'Playing...', '1000')
        playable_url = rtmp + ' playpath=' + file + ' pageUrl=' + url + ' swfUrl=' + swf + ' live=false timeout=30'
        
    print 'custom-resolver - url:' + url + ' | host:' + host + ' | id:' + id + ' | play:' + playable_url
    return playable_url        
    
def GetLinks(url):
        
    url_content = net.http_GET(url).content
    
    for link in re.finditer(r"<a.+?href=\"(.+?)\"> <b> {0,1}Watch (.+?) {0,1}</b></a>", url_content):
        playable_item_url = link.group(1)
        if '?url=' in playable_item_url:
            playable_item_url = playable_item_url[playable_item_url.index('=')+1:]
        
        hosted_media = urlresolver.HostedMediaFile(url=playable_item_url)
        ur = ' - **url-resolver**'
        if not hosted_media:
            hosted_media = IfResolverNotInURLResolverCheckHere(playable_item_url)
            ur = ''
        if hosted_media:
            playable_item_name = playable_item_url
            if re.search("http://www.", playable_item_name):
                playable_item_name = playable_item_name[playable_item_name.index('.')+1:]
            elif re.search("http://", playable_item_name):
                playable_item_name = playable_item_name.replace("http://", "")
            playable_item_name = playable_item_name[0:playable_item_name.index('.')]
            
            add_video_link(video_type, playable_item_url, title, playable_item_name.title() + " - " + link.group(2) + ur, img=img, fanart=fanart)                                    
    
def Play(url):    
    from universal import playbackengine
    
    if queued == 'true':
    
        hosted_media = urlresolver.HostedMediaFile(url=url)
        resolved_media_url = ''
        if not hosted_media:
            resolved_media_url = IfResolverNotInURLResolverResolveHere(url)
        else:
            resolved_media_url = urlresolver.resolve(url)
        
        if resolved_media_url:
            
            player = playbackengine.Play(resolved_url=resolved_media_url, addon_id=addon_id, video_type='movie', 
                                    title=title,season='', episode='', year='', watchedCallbackwithParams=WatchedCallbackwithParams,imdb_id=imdb_id)
            
            '''
            add to watch history - start
            '''
            wh = watchhistory.WatchHistory(addon_id)

            infolabels = { 'supports_meta' : 'true', 'video_type':video_type, 'name':title, 'imdb_id':imdb_id, 'season':season, 'episode':episode, 'year':year }
            
            if historylink:            
                wh.add_video_item(title + ' - ' + name, sys.argv[0]+sys.argv[2], infolabels=infolabels, img=img, is_playable=True, parent_title=historytitle)
                wh.add_directory(historytitle, historylink, infolabels=infolabels, img=img, level='1')
            else:
                wh.add_video_item(title + ' - ' + name, sys.argv[0]+sys.argv[2], infolabels=infolabels, img=img, is_playable=True)
            '''
            add to watch history - end
            '''                
                    
            player.KeepAlive()
    else:
        playbackengine.PlayInPL(title, img=img)
    
    
def ShowSearchDialog():
    last_search = addon.load_data('search')
    if not last_search: last_search = ''
    keyboard = xbmc.Keyboard()
    keyboard.setHeading('Search')
    keyboard.setDefault(last_search)
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        query = keyboard.getText()
        addon.save_data('search',query)
        GetSection(BASEURL + 'search/title/' + escape(query), '1')
    else:
        return
        
if play:
    Play(url)
    
if mode == 'main': 
    MainMenu()
elif mode == 'browse':
    Browse(section)
elif 'movies' in mode:
    Movies(section, page)
elif mode == 'section' :
    GetSection(url, page)
elif mode == 'links' :
    GetLinks(url)
elif mode == 'play':
    Play(url)
elif mode == 'resolver':
    urlresolver.display_settings()
elif mode == 'metahandlersettings':
    import metahandler
    metahandler.display_settings()
elif mode == 'favorites':
    Favorites(video_type)
elif mode == 'add_fav':
    add_favorite()
elif mode == 'del_fav':
    remove_favorite()
elif mode == 'refresh_meta':
    if video_type == VideoType_Movies:
        refresh_movie(title)
    elif video_type == VideoType_TV:
        Notify('small', 'Refresh TV Show', 'Feature not yet implemented','')
    elif video_type == VideoType_Season:
        season_refresh(title, imdb_id, season)
    elif video_type == VideoType_Episode:
        episode_refresh(title, imdb_id, season, episode)
elif mode == 'watch_mark':
    #metaget=metahandlers.MetaData()
    metaget.change_watched(video_type, title, imdb_id, season=season, episode=episode)
    xbmc.executebuiltin("Container.Refresh")
elif mode == 'universalsettings':    
    from universal import _common
    _common.addon.show_settings()
    
if not play and mode != 'resolver' and mode != 'metahandlersettings' and mode != 'universalsettings':
    addon.end_of_directory()