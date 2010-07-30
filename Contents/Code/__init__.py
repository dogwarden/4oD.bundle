# -*- coding: utf-8 -*-
###################################################################################################
#
# 4oD plugin for Plex (by sander1)
# v2.0 (July 13, 2010)
#
###################################################################################################

from PMS import *
import re, string

###################################################################################################

PLUGIN_TITLE               = '4oD'
PLUGIN_PREFIX              = '/video/4od'

BASE_URL                   = 'http://www.channel4.com'
PROGRAMMES_CATEGORIES      = '%s/programmes' % BASE_URL
PROGRAMMES_FEATURED        = '%s/programmes/4od' % BASE_URL

PROGRAMMES_BY_DATE         = '%s/programmes/4od/episode-list/date/%%s' % BASE_URL
PROGRAMMES_BY_CATEGORY     = '%s/programmes/tags/%%s/title/page-%%%%d' % BASE_URL
PROGRAMMES_BY_LETTER       = '%s/programmes/atoz/%%s/page-%%%%d' % BASE_URL
PROGRAMMES_SEARCH          = '%s/programmes/long-form-search/?q=%%s' % BASE_URL

# Default artwork and icon(s)
PLUGIN_ARTWORK             = 'art-default.png'
PLUGIN_ICON_DEFAULT        = 'icon-default.png'
PLUGIN_ICON_SEARCH         = 'icon-search.png'

###################################################################################################

def Start():
  Plugin.AddPrefixHandler(PLUGIN_PREFIX, MainMenu, PLUGIN_TITLE, PLUGIN_ICON_DEFAULT, PLUGIN_ARTWORK)
  Plugin.AddViewGroup('List', viewMode='List', mediaType='items')
  Plugin.AddViewGroup('InfoList', viewMode='InfoList', mediaType='items')

  # Set the default MediaContainer attributes
  MediaContainer.title1    = PLUGIN_TITLE
  MediaContainer.viewGroup = 'List'
  MediaContainer.art       = R(PLUGIN_ARTWORK)

  # Default icons for DirectoryItem and WebVideoItem in case there isn't an image
  DirectoryItem.thumb      = R(PLUGIN_ICON_DEFAULT)
  WebVideoItem.thumb       = R(PLUGIN_ICON_DEFAULT)

  # Set the default cache time
  HTTP.SetCacheTime(CACHE_1DAY)
  HTTP.SetHeader('User-Agent', 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.6) Gecko/20100625 Firefox/3.6.6')

###################################################################################################

def MainMenu():
  dir = MediaContainer()

  dir.Append(Function(DirectoryItem(BrowseDate, title='Browse by Date')))
  dir.Append(Function(DirectoryItem(BrowseCategory, title='Browse by Category')))
  dir.Append(Function(DirectoryItem(BrowseAZ, title='Browse Alphabetically')))
  dir.Append(Function(DirectoryItem(FeaturedCategory, title='Featured')))
  dir.Append(Function(InputDirectoryItem(Search, title='Search', prompt='Search for Programmes', thumb=R(PLUGIN_ICON_SEARCH))))

  return dir

####################################################################################################

def BrowseDate(sender):
  dir = MediaContainer(title2=sender.itemTitle)

  for i in range(30):
    date = Datetime.Now() - Datetime.Delta(days = i)
    date_key = date.strftime('%Y/%m/%d')
    date_label = date.strftime('%A %d %B')

    dir.Append(Function(DirectoryItem(Schedule, title=date_label), date=date_key))

  return dir

####################################################################################################

def Schedule(sender, date):
  dir = MediaContainer(title2=sender.itemTitle)

  programmes = XML.ElementFromURL(PROGRAMMES_BY_DATE % date, isHTML=True, errors='ignore', cacheTime=1800).xpath('//li')
  for p in programmes:
    title = p.xpath('.//a/span/text()')[0].strip()
    time = p.xpath('.//span[@class="txTime"]')[0].text.strip()
    channel = p.xpath('.//span[@class="txChannel"]')[0].text.strip()
    url = p.xpath('.//a')[0].get('href').replace('4od#', '4od/player/')
    thumb = p.xpath('.//a/img')[0].get('src').replace('106x60.jpg', '625x352.jpg')

    dir.Append(Function(WebVideoItem(PlayVideo, title=title, infolabel=time + ' / ' + channel, thumb=Function(GetThumb, url=thumb)), url=url))

  return dir

####################################################################################################

def BrowseCategory(sender):
  dir = MediaContainer(title2=sender.itemTitle)

  categories = XML.ElementFromURL(PROGRAMMES_CATEGORIES, isHTML=True, errors='ignore').xpath('/html/body//div[@id="categoryList"]//li/a')
  for c in categories:
    title = c.xpath('./span')[0].text.strip()
    tag = c.get('href').rsplit('/',1)[1]

    dir.Append(Function(DirectoryItem(Programmes, title=title), tag=tag))

  return dir

####################################################################################################

def BrowseAZ(sender):
  dir = MediaContainer(title2=sender.itemTitle)

  # A to Z
  for char in string.ascii_uppercase:
    dir.Append(Function(DirectoryItem(Programmes, title=char), char=char))

  # 0-9
  dir.Append(Function(DirectoryItem(Programmes, title='0-9'), char='0-9'))

  return dir

####################################################################################################

def Programmes(sender, tag=None, char=None):
  dir = MediaContainer(title2=sender.itemTitle)

  if tag != None:
    content_url = PROGRAMMES_BY_CATEGORY % tag
  elif char != None:
    content_url = PROGRAMMES_BY_LETTER % char.lower()

  # How many pages are there?
  numPages = len( XML.ElementFromURL(content_url % 1, isHTML=True, errors='ignore').xpath('/html/body//div[contains(@class,"pagination")][1]//*[@title="Page"]') )
  if numPages == 0:
    numPages = 1

  # Loop over the pages
  for i in range(1, numPages+1):
    programmes = XML.ElementFromURL(content_url % i, isHTML=True, errors='ignore').xpath('/html/body//a[@class="watch-on-medium"]')

    for p in programmes:
      title = p.xpath('./parent::li/h3/a/span[@class="title"]')[0].text.strip()
      url = p.get('href')
      thumb = p.xpath('./parent::li/h3/a/img')[0].get('src').replace('145x82.jpg', '625x352.jpg')

      dir.Append(Function(DirectoryItem(Series, title=title, thumb=Function(GetThumb, url=thumb)), url=url, thumb=thumb))

  if len(dir) == 0:
    dir.header = 'No contents'
    dir.message = 'This directory is empty.'

  return dir

####################################################################################################

def Series(sender, url, thumb):
  dir = MediaContainer(title2=sender.itemTitle)

  if url.find(BASE_URL) == -1:
    url = BASE_URL + url

  series = XML.ElementFromURL(url, isHTML=True, errors='ignore', cacheTime=CACHE_1HOUR).xpath('/html/body//a[contains(@class,"tab")]')
  for s in series:
    title = s.text.strip()
    id = s.get('href').strip('#')

    dir.Append(Function(DirectoryItem(Episodes, title=title, thumb=Function(GetThumb, url=thumb)), url=url, id=id))

  return dir

####################################################################################################

def Episodes(sender, url, id):
  dir = MediaContainer(viewGroup='InfoList', title2=sender.itemTitle)

  episodes = XML.ElementFromURL(url, isHTML=True, errors='ignore', cacheTime=CACHE_1HOUR).xpath('/html/body//div[@id="' + id + '"]//li')
  for e in episodes:
    title = e.xpath('.//span[@class="episodeTitle"]')[0].text.strip()
    try:
      subtitle = e.xpath('.//span[@class="episodeNumber"]')[0].text.strip()
    except:
      subtitle = ''
    summary = e.xpath('.//p[@class="synopsis formatted"]')[0].text.strip()

    try:
      broadcast = e.xpath('.//span[@class="txDate"]')[0].text.strip()
      summary += '\n\nFirst broadcast: ' + broadcast
    except:
      pass

    thumb = e.xpath('.//input[@type="hidden"]')[0].get('value')
    duration = CalculateTime( e.xpath('.//span[@class="duration"]')[0].text )
    episode_url = e.xpath('.//a[contains(@class,"popOut")]')[0].get('href')

    dir.Append(Function(WebVideoItem(PlayVideo, title=title, subtitle=subtitle, summary=summary, duration=duration, thumb=Function(GetThumb, url=thumb)), url=episode_url))

  return dir

####################################################################################################

def FeaturedCategory(sender):
  dir = MediaContainer(title2=sender.itemTitle)

  i = 0
  categories = XML.ElementFromURL(PROGRAMMES_FEATURED, isHTML=True, errors='ignore', cacheTime=CACHE_1HOUR).xpath('/html/body//li[@class="fourOnDemandSet"]')
  for c in categories:
    title = c.xpath('./h2')[0].text.strip()
    i = i + 1

    dir.Append(Function(DirectoryItem(Featured, title=title), i=i))

  return dir

####################################################################################################

def Featured(sender, i):
  dir = MediaContainer(viewGroup='InfoList', title2=sender.itemTitle)

  programmes = XML.ElementFromURL(PROGRAMMES_FEATURED, isHTML=True, errors='ignore', cacheTime=CACHE_1HOUR).xpath('/html/body//li[@class="fourOnDemandSet"][' + str(i) + ']//li')
  for p in programmes:
    url = p.xpath('./h3/a')[0].get('href')

    # Skip this item if the url doesn't contain '/4od'
    if url.find('/4od') != -1:
      title = p.xpath('./h3/a/span')[0].text.strip()
      summary = p.xpath('./p')[0].text.strip()
      thumb = p.xpath('./h3/a')[0].get('class')
      thumb = re.search('(\/[^"]+)', thumb).group(1) # Regex: start with a forward slash and catch everything except a double quote sign

      dir.Append(Function(DirectoryItem(Series, title=title, summary=summary, thumb=Function(GetThumb, url=thumb)), url=url, thumb=thumb))

  return dir

####################################################################################################

def Search(sender, query):
  dir = MediaContainer(title2=sender.itemTitle)

  result = JSON.ObjectFromURL(PROGRAMMES_SEARCH % ( String.Quote(query, usePlus=True) ))
  if len(result) > 0:
    for r in result['results']:
      title = r['value'].strip()
      url = r['siteUrl']

      try:
        thumb = XML.ElementFromURL(BASE_URL + url, isHTML=True, errors='ignore').xpath('/html/body//input[@type="hidden"]')[0].get('value')
      except:
        thumb = None

      dir.Append(Function(DirectoryItem(Series, title=title, thumb=Function(GetThumb, url=thumb)), url=url, thumb=thumb))

  if len(dir) == 0:
    dir.header = 'No results'
    dir.message = 'Your search didn\'t return any results.'

  return dir

####################################################################################################

def PlayVideo(sender, url):
  if url.find(BASE_URL) == -1:
    url = BASE_URL + url

  # '#4oDv2' is added to the url to make sure my site config is used and not an old one
  return Redirect(WebVideoItem(url + '#4oDv2'))

####################################################################################################

def GetThumb(url):
  if url.find(BASE_URL) == -1:
    url = BASE_URL + url

  data = HTTP.Request(url, cacheTime=CACHE_1MONTH)
  if data:
    return DataObject(data, 'image/jpeg')

  return Redirect(R(PLUGIN_ICON_DEFAULT))

####################################################################################################

def CalculateTime(timecode):
  milliseconds = 0
  d = re.search('([0-9]+) mins', timecode)
  milliseconds += int( d.group(1) ) * 60 * 1000
  return milliseconds