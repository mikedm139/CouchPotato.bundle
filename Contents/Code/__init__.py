import re, os
from base64 import b64encode

###################################################################################################
##
##  TODO:   ?integrate new CouchPotato API (when it is released)?
##  
###################################################################################################

APPLICATIONS_PREFIX = "/video/couchpotato"

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
    oc = ObjectContainer(view_group="InfoList", no_cache=True)

    oc.add(DirectoryObject(key=Callback(MoviesMenu), title="Manage your movies list",
        summary="View and edit your CouchPotato wanted movies list",thumb=R(ICON)))
    oc.add(DirectoryObject(key=Callback(ComingSoonMenu), title="Coming Soon",
        summary="Browse upcoming movies and add them to your wanted list", thumb=R("RT-icon.png")))
    oc.add(InputDirectoryObject(key=Callback(Search), title="Search for Movies",
        summary="Find movies to add to your wanted list", prompt="Search for", thumb=R(SEARCH_ICON),))
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
    oc = ObjectContainer(view_group="InfoList", title2="Wanted", no_cache=True)
    wantedPage = HTML.ElementFromURL(url, errors='ignore', headers=AuthHeader(), cacheTime=0)
    
    for item in wantedPage.xpath('//div[@class="item want"]'):
        try: thumb = Get_CP_URL() + item.xpath('.//img[@class="thumbnail"]')[0].get('src')
        except: thumb = ''
        title = item.xpath('./span/span/h2')[0].text
        try: summary = item.xpath('.//span[@class="overview"]')[0].text
        except: summary = 'No Overview'
        try: rating = item.xpath('./span[@class="rating"]')[0].text
        except: rating = 'No Rating'
        year = item.xpath('.//span[@class="year"]')[0].text
        dataID = item.xpath('.')[0].get('data-id')
        title = title + ' (%s)' % year
        oc.add(PopupDirectoryObject(key=Callback(WantedList, dataID=dataID), title=title, summary=summary, thumb=Callback(GetThumb, url=thumb)))
    
    return oc
  
################################################################################

def WaitingMenu():
    '''Scrape waiting movies from CouchPotato and populate the list with results.
        Note: waiting movies differ from wanted movies only by one tag'''
    url = Get_CP_URL() + '/movie/'
    oc = ObjectContainer(view_group="InfoList", title2="Waiting", no_cache=True)
    wantedPage = HTML.ElementFromURL(url, errors='ignore', headers=AuthHeader(), cacheTime=0)
    
    for item in wantedPage.xpath('//div[@class="item waiting"]'):
        try: thumb = Get_CP_URL() + item.xpath('.//img[@class="thumbnail"]')[0].get('src')
        except: thumb = ''
        title = item.xpath('./span/span/h2')[0].text
        try: summary = item.xpath('.//span[@class="overview"]')[0].text
        except: summary = 'No Overview'
        try: rating = item.xpath('./span[@class="rating"]')[0].text
        except: rating = 'No Rating'
        year = item.xpath('.//span[@class="year"]')[0].text
        dataID = item.xpath('.')[0].get('data-id')
        title = title + ' (%s)' % year
        oc.add(PopupDirectoryObject(key=Callback(WantedList, dataID=dataID), title=title, summary=summary, thumb=Callback(GetThumb, url=thumb)))
    
    return oc
  
################################################################################

def SnatchedMenu():
    '''Scrape snatched movies from CouchPotato and populate the list with results'''
    url = Get_CP_URL() + '/movie/'
    oc = ObjectContainer(view_group="InfoList", title2="Snatched", no_cache=True)
    wantedPage = HTML.ElementFromURL(url, errors='ignore', cacheTime=0)
    thumb = R(SNATCHED_ICON)
    summary = 'This movie should now appear in your downloads queue.'
    
    for item in wantedPage.xpath('//div[@id="snatched"]/span'):
        #Log('parsing movie item')
        title = item.text.replace('\n','').replace('\t','')
        dataID = item.xpath('.//a[@class="reAdd"]')[0].get('data-id')
        #Log('Parsing ' + title)
        oc.add(PopupDirectoryObject(key=Callback(SnatchedList, dataID=dataID), title=title, summary=summary, thumb = Resource.ContentsOfURLWithFallback(url=thumb, fallback='no_poster.jpg')))
    
    return oc
  
################################################################################

def DownloadedMenu():
    '''Scrape downloaded movies from CouchPotato and populate the list with results'''
    url = Get_CP_URL() + '/movie/'
    oc = ObjectContainer(view_group="InfoList", title2="Downloaded", no_cache=True)
    wantedPage = HTML.ElementFromURL(url, errors='ignore', headers=AuthHeader(), cacheTime=0)
    thumb = R(DL_ICON)
    summary = 'This movie should now be available in your Plex library.'
    
    for item in wantedPage.xpath('//div[@id="downloaded"]/span'):
        title = item.text.replace('\n','').replace('\t','')
        #Log('Parsing ' + title)
        dataID = item.xpath('./a')[1].get('data-id')
        oc.add(PopupDirectoryObject(key=Callback(SnatchedList, dataID=dataID), title=title, summary=summary, thumb = Resource.ContentsOfURLWithFallback(url=thumb, fallback='no_poster.jpg')))
    
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
    return ObjectContainer(header="CouchPotato", message=L('Deleting from wanted list'), no_history=True)

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

def Search(query):
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
                try:
                    year = str(Datetime.ParseDate(releaseDate).year)
                    movieTitle = "%s (%s)" % (movieTitle, year)
                except: year = None
            else:
                year = None
            overview = movie.find('overview').text
            try:
                posterUrl = movie.xpath('.//image[@type="poster"]')[-1].get('url')
            except:
                posterUrl = ''
        
            if year != None:
                title = "%s (%s)" % (movieTitle, year)
                #Log(movieTitle + ' ('+year+') ' + ' found'),
                oc.add(PopupDirectoryObject(key=Callback(AddMovieMenu, id=imdbID, year=year, provider="TMDB"),
                        title=movieTitle, summary=overview, thumb=Callback(GetThumb, url=posterUrl)))
                resultCount = resultCount+1
    return oc
    
################################################################################

def AddMovieMenu(id, year, url="", youtubeID=None, provider=""):
    '''Display an action/context menu for the selected movie'''
    oc = ObjectContainer()
    oc.add(DirectoryObject(key=Callback(AddMovie, id=id, year=year), title='Add to Wanted list'))
    oc.add(DirectoryObject(key=Callback(QualitySelectMenu, id=id, year=year), title='Select quality to add'))
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

def UpdateMenu():
    '''Display the CouchPotato Updater popup menu'''
    
    oc = ObjectContainer()
    oc.add(PopupDirectoryObject(key=Callback(UpdateNow), title='Update CouchPotato Now'))
    
    return oc

################################################################################

def UpdateNow(sender):
    '''Tell CouchPotato to run the updater'''
    url = Get_CP_URL()  + '/config/update/'
    try:
        runUpdate = HTTP.Request(url, errors='ignore', headers=AuthHeader()).content
    except:
        pass
    time.sleep(10)
    return ObjectContainer(header='CouchPotato', message=L('Update completed successfully'))

################################################################################

def Get_CP_URL():
  return 'http://'+Prefs['cpIP']+':'+Prefs['cpPort']

################################################################################

def QualitySelectMenu(id, year):
    '''provide an option to select a quality other than default before adding a movie'''
    
    oc = ObjectContainer()
    
    url = Get_CP_URL() + '/movie/'
    for quality in HTML.ElementFromURL(url, headers=AuthHeader()).xpath('//form[@id="addNew"]/div/select/option'):
        value = quality.get('value')
        name = quality.text
        oc.add(DirectoryObject(key=Callback(AddWithQuality, id=id, year=year,
            quality=value), title=name, summary='Add movie with '+name+' quality', thumb=R(ICON)))
    
    return oc

################################################################################

def AddWithQuality(id, year, quality):   
    '''tell CouchPotato to add the given movie with the given quality (rather than
        the defaultQuality)'''
    
    url = Get_CP_URL() + '/movie/'
    post_values = {'quality' : quality, 'add' : "Add"}

    # tell CouchPotato to add the given movie
    moviedAdded = HTTP.Request(url+'imdbAdd/?id='+id+'&year='+year, post_values, headers=AuthHeader())
    
    return ObjectContainer(header="CouchPotato", message=L("Added to Wanted list."), no_history=True)
    
####################################################################################################
####################################################################################################
####################################################################################################


RT_API_KEY = 'bnant4epk25tfe8mkhgt4ezg'

RT_LIST_URL = 'http://api.rottentomatoes.com/api/public/v1.0/lists/%s.json?apikey=%s'

####################################################################################################

def ComingSoonMenu():
    oc = ObjectContainer(title2="Coming Soon")
    oc.add(DirectoryObject(key=Callback(ComingMoviesListMenu, list_type="movies"), title="Theatres", thumb=R("RT-icon.png")))
    oc.add(DirectoryObject(key=Callback(ComingMoviesListMenu, list_type="dvds"), title="DVD", thumb=R("RT-icon.png")))
    return oc

def ComingMoviesListMenu(list_type):
    oc = ObjectContainer()
    if list_type == "movies":
        oc.title2="Theaters"
    elif list_type == "dvds":
        oc.title2 == "DVD"
    
    movieLists = JSON.ObjectFromURL(RT_LIST_URL % (list_type, RT_API_KEY))
    for movie_list in movieLists['links']:
        name = movie_list
        title = String.CapitalizeWords(name.replace('_', ' '))
        url = movieLists['links'][name]
        oc.add(DirectoryObject(key=Callback(ComingMoviesList, title=title, url=url), title=title, thumb=R(ICON)))
    return oc
  
def ComingMoviesList(title, url=None):
    oc = ObjectContainer(title2=title, view_group="InfoList")
    
    movies = JSON.ObjectFromURL(url + '?apikey=%s' % RT_API_KEY)
    
    for movie in movies['movies']:
        title = "%s (%s)" % (movie['title'], movie['year'])
        summary = BuildSummary(movie)
        thumb= movie['posters']['original']
        
        oc.add(PopupDirectoryObject(key=Callback(DetailsMenu, movie=movie), title=title, summary=summary, thumb = Resource.ContentsOfURLWithFallback(url=thumb, fallback='no_poster.jpg')))
    return oc

def DetailsMenu(movie):
    oc = ObjectContainer(title2=movie['title'])
    thumb = movie['posters']['original']
    oc.add(DirectoryObject(key=Callback(AddMovie, id=movie['alternate_ids']['imdb'], year=str(movie['year'])), title='Add to Wanted list', thumb = Resource.ContentsOfURLWithFallback(url=thumb, fallback='no_poster.jpg')))
    oc.add(DirectoryObject(key=Callback(QualitySelectMenu, id=movie['alternate_ids']['imdb'], year=str(movie['year'])), title='Select quality to add', thumb = Resource.ContentsOfURLWithFallback(url=thumb, fallback='no_poster.jpg')))
    oc.add(DirectoryObject(key=Callback(ReviewsMenu, title=movie['title'], url=movie['links']['reviews']), title="Read Reviews", thumb = Resource.ContentsOfURLWithFallback(url=thumb, fallback='no_poster.jpg')))
    oc.add(DirectoryObject(key=Callback(TrailersMenu, title=movie['title'], url=movie['links']['clips']), title="Watch Trailers", thumb = Resource.ContentsOfURLWithFallback(url=thumb, fallback='no_poster.jpg')))
    oc.add(DirectoryObject(key=Callback(ComingMoviesList, title=movie['title'], url=movie['links']['similar']), title="Find Similar Movies", thumb = Resource.ContentsOfURLWithFallback(url=thumb, fallback='no_poster.jpg')))
    return oc

def ReviewsMenu(title, url):
    oc = ObjectContainer(title1=title, title2="Reviews", view_group="InfoList")
    reviews = JSON.ObjectFromURL(url +'?apikey=%s' % RT_API_KEY)['reviews']
    for review in reviews:
        title = "%s - %s" % (review['critic'], review['publication'])
        try: score = review['original_score']
        except: score = 'N/A'
        summary = "Rating: %s\n\n%s" % (score, review['quote'])
        oc.add(DirectoryObject(key=Callback(DoNothing), title=title, summary=summary, thumb=None))
    return oc

def TrailersMenu(title, url):
    oc = ObjectContainer(title1=title, title2="Trailers", view_group="InfoList")
    trailers = JSON.ObjectFromURL(url +'?apikey=%s' % RT_API_KEY)['clips']
    for trailer in trailers:
        #Log(trailer)
        title = trailer['title']
        thumb = trailer['thumbnail']
        duration = int(trailer['duration'])*1000
        url = trailer['links']['alternate']
        oc.add(VideoClipObject(url=url, title=title, duration=duration, thumb = Resource.ContentsOfURLWithFallback(url=thumb, fallback='no_poster.jpg')))
    return oc

def GetCast(cast):
    actors = ''
    for actor in cast:
        name = actor['name']
        try: role = actor['characters'][0]
        except: role = ''
        actors = actors + '%s - %s\n' % (name, role)
    return actors

def GetReleaseDates(movie):
    try: theater = movie['release_dates']['theater']
    except: theater = 'N/A'
    try: dvd = movie['release_dates']['dvd']
    except: dvd = 'N/A'
    return "Theater: %s\nDVD: %s" % (theater, dvd)

def BuildSummary(movie):
    critic_rating = movie['ratings']['critics_score']
    if critic_rating == -1:
        critic_rating = "None"
    audience_rating = movie['ratings']['audience_score']
    cast = GetCast(movie['abridged_cast'])
    synopsis = movie['synopsis']
    content_rating = movie['mpaa_rating']
    runtime = movie['runtime']
    release_dates = GetReleaseDates(movie)
    summary = 'Runtime: %s minutes\nMPAA: %s\nCritic Rating: %s\nAudience Rating: %s\nRelease:\n%s\n\nSynopsis:\n%s\n\nCast:\n%s' % (runtime, content_rating, critic_rating, audience_rating, release_dates, synopsis, cast)
    return summary

def DoNothing():
    ###Exactly like the function says###
    return

