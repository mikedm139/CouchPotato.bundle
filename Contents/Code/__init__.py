import re, os
from base64 import b64encode

###################################################################################################
##
##  TODO:   ?integrate new CouchPotato API (when it is released)?
##  
###################################################################################################

APPLICATIONS_PREFIX = "/applications/couchpotato"

NAME = L('CouchPotato')

ART           = 'art-default.jpg'
ICON          = 'icon-default.png'
SEARCH_ICON   = 'icon-search.png'
PREFS_ICON    = 'icon-prefs.png'
SNATCHED_ICON = 'sab-icon.png'
DL_ICON       = 'Plex_256x256.png'
MOVIE_ICON    = 'movie-reel.jpg'
THEATRE_ICON  = 'popcorn.jpg'
BD_ICON       = 'BD_icon.jpg'

####################################################################################################

def Start():
    '''Setup plugin for use'''
    if Dict['MovieSectionID'] == None:
        Plugin.AddPrefixHandler(APPLICATIONS_PREFIX, GetMovieSectionID, NAME, ICON, ART)
    else:
        Plugin.AddPrefixHandler(APPLICATIONS_PREFIX, MainMenu, NAME, ICON, ART)
    
    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = NAME
    DirectoryObject.thumb = R(ICON)
    HTTP.CacheTime=3600

####################################################################################################

def AuthHeader():
    header = {}

    if Prefs['cpUser'] and Prefs['cpPass']:
        header = {'Authorization': 'Basic ' + b64encode(Prefs['cpUser'] + ':' + Prefs['cpPass'])}

    return header

####################################################################################################

def ValidatePrefs():
    #if Prefs['cpUser'] and Prefs['cpPass']:
    #    HTTP.SetPassword(url=Get_CP_URL(), username=Prefs['cpUser'], password=Prefs['cpPass'])
    return

####################################################################################################

def MainMenu():
    '''Populate main menu options'''
    oc = ObjectContainer(view_group="InfoList", title="CouchPotato", noCache=True)

    oc.add(DirectoryObject(key=Callback(MoviesMenu), title="Manage your movies list",
        summary="View and edit your CouchPotato wanted movies list",thumb=R(ICON)))
    #oc.add(DirectoryObject(key=Callback(ComingSoonMenu), title="Coming Soon",
    #    summary="Browse upcoming movies and add them to your wanted list",thumb=R(ICON)))
    oc.add(InputDirectoryObject(key=Callback(SearchResults), title="Search for Movies",
        summary="Find movies to add to your wanted list",thumb=R(SEARCH_ICON)))
    oc.add(PrefsObject(title="Preferences", summary="Set prefs to allow plugin to connect to CouchPotato app",thumb=R(PREFS_ICON)))
    if UpdateAvailable():
        Log('Update available')
        oc.add(PopupDirectoryObject(key=Callback(UpdateMenu), title='CouchPotato update available',
            summary='Update your CouchPotato install to the newest version', thumb=R(ICON)))

    return oc

################################################################################

def MoviesMenu():
    '''Populate the movies menu with available options'''
    oc = ObjectContainer(view_group="InfoList", title2="Wanted Movies")

    oc.add(DirectoryObject(key=Callback(WantedMenu), title="Wanted List",
        summary="CouchPotato is watching for these movies",thumb=R(ICON)))
    oc.add(DirectoryObject(key=Callback(WaitingMenu), title="Waiting List",
        summary='CouchPotato has found these movies but not in your defined "archive" quality, so it is still watching for better quality versions.', thumb=R(ICON)))
    oc.add(DirectoryObject(key=Callback(SnatchedMenu), title="Snatched List",
        summary="CouchPotato has found these movies and is waiting for them to be downloaded.", thumb=R(SNATCHED_ICON)))
    oc.add(DirectoryObject(key=Callback(DownloadedMenu), title="Downloaded",
        summary="CouchPotato has found and downloaded all these movies in the quality you requested. They should be available in your Plex library.", thumb=R(DL_ICON)))
    return oc
    
################################################################################

def WantedMenu():
    '''Scrape wanted movies from CouchPotato and populate the list with results'''
    url = Get_CP_URL()  + '/movie/'
    oc = ObjectContainer(view_group="InfoList", title2="Wanted", noCache=True)
    wantedPage = HTML.ElementFromURL(url, errors='ignore', headers=AuthHeader(), cacheTime=0)
    
    for item in wantedPage.xpath('//div[@class="item want"]'):
        thumb = Get_CP_URL() + item.xpath('.//img[@class="thumbnail"]')[0].get('src')
        title = item.xpath('./span/span/h2')[0].text
        try: summary = item.xpath('.//span[@class="overview"]')[0].text
        except: summary = 'No Overview'
        try: rating = item.xpath('./span[@class="rating"]')[0].text
        except: rating = 'No Rating'
        year = item.xpath('.//span[@class="year"]')[0].text
        dataID = item.xpath('.')[0].get('data-id')
        oc.add(PopupDirectoryObject(key=Callback(WantedList, dataID=dataID), title=title, year=year, summary=summary, thumb=Callback(GetThumb, url=thumb)))
    
    return oc
  
################################################################################

def WaitingMenu():
    '''Scrape waiting movies from CouchPotato and populate the list with results.
        Note: waiting movies differ from wanted movies only by one tag'''
    url = Get_CP_URL() + '/movie/'
    oc = ObjectContainer(view_group="InfoList", title2="Waiting", noCache=True)
    wantedPage = HTML.ElementFromURL(url, errors='ignore', headers=AuthHeader(), cacheTime=0)
    
    for item in wantedPage.xpath('//div[@class="item waiting"]'):
        thumb = Get_CP_URL() + item.xpath('.//img[@class="thumbnail"]')[0].get('src')
        title = item.xpath('./span/span/h2')[0].text
        try: summary = item.xpath('.//span[@class="overview"]')[0].text
        except: summary = 'No Overview'
        try: rating = item.xpath('./span[@class="rating"]')[0].text
        except: rating = 'No Rating'
        year = item.xpath('.//span[@class="year"]')[0].text
        dataID = item.xpath('.')[0].get('data-id')
        oc.add(PopupDirectoryObject(key=Callback(WantedList, dataID=dataID), title=title, year=year, summary=summary, thumb=Callback(GetThumb, url=thumb)))
    
    return oc
  
################################################################################

def SnatchedMenu():
    '''Scrape snatched movies from CouchPotato and populate the list with results'''
    url = Get_CP_URL() + '/movie/'
    oc = ObjectContainer(view_group="InfoList", title2="Snatched", noCache=True)
    wantedPage = HTML.ElementFromURL(url, errors='ignore', cacheTime=0)
    thumb = R(SNATCHED_ICON)
    summary = 'This movie should now appear in your downloads queue.'
    
    for item in wantedPage.xpath('//div[@id="snatched"]/span'):
        #Log('parsing movie item')
        title = item.text.replace('\n','').replace('\t','')
        #Log('Parsing ' + title)
        oc.add(PopupDirectoryObject(key=Callback(SnatchedList, dataID=dataID), title=title, summary=summary, thumb=thumb))
    
    return oc
  
################################################################################

def DownloadedMenu():
    '''Scrape downloaded movies from CouchPotato and populate the list with results'''
    url = Get_CP_URL() + '/movie/'
    oc = ObjectContainer(view_group="InfoList", title2="Downloaded", noCache=True)
    wantedPage = HTML.ElementFromURL(url, errors='ignore', headers=AuthHeader(), cacheTime=0)
    thumb = R(DL_ICON)
    summary = 'This movie should now be available in your Plex library.'
    
    for item in wantedPage.xpath('//div[@id="downloaded"]/span'):
        title = item.text.replace('\n','').replace('\t','')
        #Log('Parsing ' + title)
        dataID = item.xpath('./a')[1].get('data-id')
        oc.add(PopupDirectoryObject(key=Callback(SnatchedList, dataID=dataID), title=title, summary=summary, thumb=thumb))
    
    return oc
  
################################################################################

def WantedList(dataID):
    '''Display an action-context menu for the selected movie'''
    oc = ObjectContainer(title2="Wanted Movies")
    oc.add(DirectoryObject(key=Callback(ForceRefresh, dataID=dataID), title='Refresh'))
    oc.add(DirectoryObject(key=Callback(RemoveMovie, dataID=dataID), title='Delete'))
    return oc

################################################################################

def SnatchedList(dataID):
    '''Display an action-context menu for the selected movie'''
    oc = ObjectContainer()
    oc.add(DirectoryObject(key=Callback(DownloadComplete, dataID=dataID), title='Mark Download Complete'))
    oc.add(DirectoryObject(key=Callback(FailedRetry, dataID=dataID), title='Failed - Try Again'))
    oc.add(DirectoryObject(key=Callback(FailedFindNew, dataID=dataID), title='Failed - Find New Source'))
    return oc

################################################################################

def ForceRefresh(dataID):
    '''Force CouchPotato to refresh info and search for the selected movie'''
    url = Get_CP_URL() + '/cron/forceSingle/?id=' + dataID
    #Log('Forcecheck url: ' + url)
    result = HTTP.Request(url, headers=AuthHeader()).content
    return ObjectContainer(header="CouchPotato", message=L('Forcing refresh/search'), no_history=True)

################################################################################

def RemoveMovie(dataID):
    '''Tell CouchPotato to remove the selected movie from the wanted list'''
    url = Get_CP_URL() + '/movie/delete/?id=' + dataID
    #Log('DeleteMovie url: ' + url)
    result = HTTP.Request(url, headers=AuthHeader()).content
    return ObjectContainer(header="CouchPotato", meddage=L('Deleting from wanted list'), no_history=True)

################################################################################

def DownloadComplete(dataID):
    '''Tell CouchPotato to mark the selected movie as a completed download'''
    url = Get_CP_URL() + '/movie/downloaded/?id=' + dataID
    #Log('Downloaded url: ' + url)
    result = HTTP.Request(url, headers=AuthHeader()).content
    return ObjectContainer(header="CouchPotato", message=L('Marked Download Complete'), no_history=True)

################################################################################

def FailedRetry(dataID):
    '''Tell CouchPotato to mark the selected movie as a failed download and retry using the same file'''
    url = Get_CP_URL() + '/movie/reAdd/?id=' + dataID
    #Log('Retry url: ' + url)
    result = HTTP.Request(url, headers=AuthHeader()).content
    return ObjectContainer(header="CouchPotato", message=L('Downloaded re-added to queue'), no_history=True)

################################################################################

def FailedFindNew(dataID):
    '''Tell CouchPotato to mark the selected movie as a failed download and find a different file to retry'''
    url = Get_CP_URL() + '/movie/reAdd/?id=' + dataID + '&failed=true'
    #Log('FindNew url: ' + url)
    result = HTTP.Request(url, headers=AuthHeader()).content
    return ObjectContainer(header="CouchPotato", message=L('Movie re-added to "Wanted" list'), no_history=True)

################################################################################

def SearchResults(query):
    '''Search themoviedb.org for movies using user input, and populate a list with the results'''
    oc = ObjectContainer(title2="Search Results", view_group="InfoList")
    #Log('Search term(s): ' + query)
    
    resultList = XML.ElementFromURL(
        'http://api.themoviedb.org/2.1/Movie.search/en/xml/9b939aee0aaafc12a65bf448e4af9543/' +
        String.Quote(query, usePlus=False))
    
    resultCount = 0
    
    for movie in resultList.xpath('//movie'):
        if resultCount < 10:
            movieTitle = movie.find("name").text
            imdbID = movie.find('imdb_id').text
            releaseDate = movie.find('released').text
            if releaseDate != '1900-01-01':
                try: year = str(Datetime.ParseDate(releaseDate).year)
                except: year = None
            else:
                year = None
            overview = movie.find('overview').text
            try:
                posterUrl = movie.xpath('.//image[@type="poster"]')[-1].get('url')
            except:
                posterUrl = 'http://hwcdn.themoviedb.org/images/no-poster.jpg'
            link = movie.find('url').text
            #Log(link)
            try:
                trailerText = HTML.ElementFromURL(link).xpath('//p[@class="trailers"]')[0].text
                if trailerText == "No ":
                    link = ""
            except:
                link = ""    
        
            if year != None:
                Log(movieTitle + ' ('+year+') ' + ' found'),
                oc.add(PopupDirectoryObject(key=Callback(AddMovieMenu, id=imdbID, year=year, url=link, provider="TMDB"),
                        title=movieTitle, subtitle=year, summary=overview, thumb=Function(GetThumb, url=posterUrl)))
                resultCount = resultCount+1
    return oc
    
################################################################################

def AddMovieMenu(id, year, url="", youtubeID=None, provider=""):
    '''Display an action/context menu for the selected movie'''
    oc = ObjectContainer()
    oc.add(DirectoryObject(key=Callback(AddMovie, id=id, year=year), title='Add to Wanted list'))
    oc.add(DirectoryObject(key=Callback(QualitySelectMenu, id=id, year=year), title='Select quality to add'))
    #if url != "":
    #    oc.add(DirectoryObject(key=Callback(TrailerMenu, url=url, provider=provider), title='Watch A Trailer'))
    return oc

################################################################################

def AddMovie(id, year):
    '''Tell CouchPotato to add the selected movie to the wanted list'''
    url = Get_CP_URL() + '/movie/'
    defaultQuality = HTML.ElementFromURL(url, headers=AuthHeader()).xpath('//form[@id="addNew"]/div/select/option')[0].get('value')
    post_values = {'quality' : defaultQuality, 'add' : "Add"}

    # tell CouchPotato to add the given movie
    moviedAdded = HTTP.Request(url+'imdbAdd/?id='+id+'&year='+year, post_values, headers=AuthHeader())
    
    return ObjectContainer(header="CouchPotato", message=L("Added to Wanted list."), no_history=True)

################################################################################
#
#def ComingSoonMenu(sender):
#    dir = MediaContainer(title2="Coming Soon")
#    dir.Append(Function(DirectoryItem(ComingToTheatres, title="Coming to Theatres", thumb=R(THEATRE_ICON))))
#    dir.Append(Function(DirectoryItem(ComingToBluray, title="Coming to Bluray", thumb=R(BD_ICON))))
#    dir.Append(Function(DirectoryItem(NewReleases,"New on DVD/BluRay", thumb=R(ICON))))
#    
#    return dir
#
################################################################################
#
#def ComingToTheatres(sender):
#    '''Scrape themovieinsider.com for coming soon movies and populate a list'''
#    url = 'http://www.themovieinsider.com/movies/coming-soon/'
#    dir = MediaContainer(viewGroup="InfoList", title2="Coming Soon", noCache=True)
#    comingSoonPage = HTML.ElementFromURL(url, errors='ignore')
#    
#    for comingMovie in comingSoonPage.xpath('//h3'):
#        link = comingMovie.xpath('./a')[0].get('href')
#        movieName = comingMovie.xpath('./a')[0].text
#        movieInfoPage = HTML.ElementFromURL(link, errors='ignore')
#        try:
#            movieTagLine = movieInfoPage.xpath('//p[@id="tagline"]')[0].text
#            Log(movieTagLine)
#        except:
#            movieTagLine = ''
#        movieYear = movieInfoPage.xpath('//table[@id="profileData"]/tr/td/a')[1].text
#        Log(movieYear)
#        try:
#            movieOverview = movieInfoPage.xpath('//div[@id="synopsis"]/text()')[0]
#            Log(movieOverview)
#        except:
#            movieOverview = ''
#        try:
#            imdbLink = movieInfoPage.xpath('//div[@id="relatedLinks"]/ul/li/a')[0].get('href')
#            imdbID = str(imdbLink)[26:-1]
#            Log(imdbID)
#        except:
#            continue
#        dir.Append(Function(PopupDirectoryItem(AddMovieMenu,
#                title=(movieName+' ('+movieYear+')'),
#                subtitle=movieTagLine,
#                summary = movieOverview,
#                thumb = Function(GetThumb, link=link)),
#            id=imdbID, year=movieYear, url=link, provider="MovieInsider"))
#        
#    return dir
#
################################################################################
#
#def ComingToBluray(sender):
#    '''Scrape themovieinsider.com for coming soon movies and populate a list'''
#    url = 'http://www.themovieinsider.com/blu-rays/coming-soon/'
#    dir = MediaContainer(viewGroup="InfoList", title2="Coming Soon", noCache=True)
#    comingSoonPage = HTML.ElementFromURL(url, errors='ignore')
#    
#    for comingMovie in comingSoonPage.xpath('//h3'):
#        link = comingMovie.xpath('./a')[0].get('href')
#        movieName = comingMovie.xpath('./a')[0].text
#        movieInfoPage = HTML.ElementFromURL(link,errors='ignore')
#        try:
#            movieTagLine = movieInfoPage.xpath('//p[@id="tagline"]')[0].text
#            Log(movieTagLine)
#        except:
#            movieTagLine = ''
#        movieYear = movieInfoPage.xpath('//table[@id="profileData"]/tr/td/a')[1].text
#        try:
#            movieOverview = movieInfoPage.xpath('//div[@id="synopsis"]/text()')[0]
#        except:
#            movieOverview = ""
#        try:
#            imdbLink = movieInfoPage.xpath('//div[@id="relatedLinks"]/ul/li/a')[0].get('href')
#            imdbID = str(imdbLink)[26:-1]
#        except:
#            continue
#        dir.Append(Function(PopupDirectoryItem(AddMovieMenu,
#                title=(movieName+' ('+movieYear+')'),
#                subtitle=movieTagLine,
#                summary = movieOverview,
#                thumb = Function(GetThumb, link=link)),
#            id=imdbID, year=movieYear, url=link, provider="MovieInsider"))
#        
#    return dir
#
################################################################################
#
#def NewReleases(sender):
#    '''Scrape PopularNewReleases.com for recent BluRay releases'''
#    url = 'http://popularnewreleases.com/index.php?sort=release-date'
#    dir = MediaContainer(viewGroup="InfoList", title2="New Releases", noCache=True)
#    newReleasePage = HTML.ElementFromURL(url, errors='ignore')
#    
#    for movie in newReleasePage.xpath('//table[@class="movie"]'):
#        movieTitle = movie.xpath('.//h1[@class="title"]/a')[0].text
#        Log('Found - New Release: '+movieTitle)
#        try: posterUrl = movie.xpath('.//img[@class="movieart"]')[0].get('src')
#        except: posterUrl = 'http://hwcdn.themoviedb.org/images/no-poster.jpg'
#        try:
#            youtubetrailer=movie.xpath('.//a[@class="trailer-link internal-action-link"]')[0].get('youtubeid')
#        except:
#            youtubetrailer=None
#        Log('YouTubeID: '+str(youtubetrailer))
#        try:
#            BDReleaseDate = movie.xpath('.//td[@class="on-video"]')[0].text
#        except:
#            BDReleaseDate = ""    
#        movieYear = movie.xpath('.//span[@class="theatrical-release-year"]')[0].text.split('(')[1].split(')')[0]
#        Log('Release year: '+movieYear)
#        try:
#            movieOverview = movie.xpath('.//p[@class="synopsis"]')[0].text
#        except:
#            movieOverview = ""
#        imdbID = movie.xpath('.//a[@class="external-action-link"]')[0].get('href').split('title/tt')[1]
#            
#        Log('imdbID: ' + imdbID)
#        dir.Append(Function(PopupDirectoryItem(AddMovieMenu,
#                title=(movieTitle+' ('+movieYear+')'),
#                subtitle=('Release: '+BDReleaseDate),
#                summary = movieOverview,
#                thumb = Function(GetThumb, url=posterUrl)),
#            id=imdbID, year=movieYear, youtubeID=youtubetrailer, provider="MovieInsider"))
#        
#    return dir
#
################################################################################
#
#def TrailerMenu(sender, url="", youtubeID=None, provider=""):
#    '''Display a list of WebVideoItem trailers for the selected movie (coming soon menu and *maybe search menu)'''
#        
#    cookies = HTTP.GetCookiesForURL('http://www.youtube.com')
#
#    dir = MediaContainer(ViewGroup="InfoList", title2="Trailers", httpCookies=cookies, noCache=True)
#       
#    if provider == "MovieInsider":
#        for trailer in HTML.ElementFromURL(url).xpath('//div[@id="trailer"]/a'):
#            trailerID = str(trailer.xpath('div')[0].get('style'))[44:-14]
#            trailerThumb = str(trailer.xpath('div')[0].get('style'))[21:-2]
#            trailerTitle = trailer.xpath('div/p/ins[@class="icon play"]/parent::p/text()')[0]
#            #Log(trailerTitle)
#            dir.Append(Function(WebVideoItem(YtPlayVideo,
#                    title=trailerTitle,
#                    thumb=trailerThumb),
#                video_id=trailerID))
#    
#    elif provider == "TMDB":
#        for trailer in HTML.ElementFromURL(url).xpath('//p[@class="trailers"]/a'):
#            trailerID = str(trailer.get('href'))[31:-5]
#            #Log('TrailerID: '+trailerID)
#            thumbUrl = 'http://i2.ytimg.com/vi/'+trailerID+'/default.jpg'
#            trailerTitle = trailer.text
#            #Log(trailerTitle)
#            dir.Append(Function(WebVideoItem(YtPlayVideo,
#                    title=trailerTitle,
#                    thumb=Function(GetThumb, url=thumbUrl)),
#                video_id=trailerID))
#            
#    elif provider == "PopularNewReleases":
#        thumbUrl = 'http://i2.ytimg.com/vi/%s/default.jpg' % youtubeID
#        dir.Append(Function(WebVideoItem(YtPlayVideo, title='Trailer',
#            thumb=Function(GetThumb, url=thumbUrl)), video_id=youtubeID))
#
#    else: pass
#    
#    return dir
#    
################################################################################

def GetThumb(url=None, link=None):
    '''A function to return thumbs.'''
    if link:
        try: url = HTML.ElementFromURL(link,errors='ignore').xpath('//img[@id="poster"]')[0].get('src')
        except: url = 'http://hwcdn.themoviedb.org/images/no-poster.jpg'
    else:
        pass
    try:
        data = HTTP.Request(url, cacheTime=CACHE_1MONTH)
        return DataObject(data, 'image/jpeg')
    except:
        data = HTTP.Request('http://hwcdn.themoviedb.org/images/no-poster.jpg', cacheTime=CACHE_1MONTH)
        return DataObject(data, 'image/jpeg')
        
################################################################################

def UpdateAvailable():
    '''Check for updates to CouchPotato using the update flag on the webUI'''
    Log('Running function "UpdateAvailable()"')
    url = Get_CP_URL() + '/movie/'
    
    try:
        cpPage = HTML.ElementFromURL(url, errors='ignore', cacheTime=0, headers=AuthHeader())
    except:
        Log('Unable to access CouchPotato webserver. Please check plugin preferences.')
        return False
    try:
        Log(cpPage.xpath('//span[@class="updateAvailable git"]')[0].text)
        if cpPage.xpath('//span[@class="updateAvailable git"]')[0].text == 'Update (':
            cpUpdate = True
        else:
            cpUpdate = False
    except:
        cpUpdate = False
    #Log(cpUpdate)
    
    return cpUpdate
    
################################################################################

def UpdateMenu(sender):
    '''Display the CouchPotato Updater popup menu'''
    
    dir = MediaContainer()
    dir.Append(Function(PopupDirectoryItem(UpdateNow, title='Update CouchPotato Now')))
    
    return dir

################################################################################

def UpdateNow(sender):
    '''Tell CouchPotato to run the updater'''
    url = Get_CP_URL()  + '/config/update/'
    try:
        runUpdate = HTTP.Request(url, errors='ignore', headers=AuthHeader()).content
    except:
        pass
    time.sleep(10)
    return MessageContainer('CouchPotato', L('Update completed successfully'))

################################################################################

def Get_CP_URL():
  return 'http://'+Prefs['cpIP']+':'+Prefs['cpPort']

################################################################################

def QualitySelectMenu(sender, id, year):
    '''provide an option to select a quality other than default before adding a movie'''
    
    dir = MediaContainer()
    
    url = Get_CP_URL() + '/movie/'
    for quality in HTML.ElementFromURL(url, headers=AuthHeader()).xpath('//form[@id="addNew"]/div/select/option'):
        value = quality.get('value')
        name = quality.text
        dir.Append(Function(DirectoryItem(AddWithQuality, title=name,
            subtitle='Add movie with '+name+' quality', thumb=R(ICON)), id=id, year=year,
            quality=value))
    
    return dir

################################################################################

def AddWithQuality(sender, id, year, quality):   
    '''tell CouchPotato to add the given movie with the given quality (rather than
        the defaultQuality)'''
    
    url = Get_CP_URL() + '/movie/'
    post_values = {'quality' : quality, 'add' : "Add"}

    # tell CouchPotato to add the given movie
    moviedAdded = HTTP.Request(url+'imdbAdd/?id='+id+'&year='+year, post_values, headers=AuthHeader())
    
    return MessageContainer("CouchPotato", L("Added to Wanted list."))