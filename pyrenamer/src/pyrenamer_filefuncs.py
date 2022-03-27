# -*- coding: utf-8 -*-

"""
Copyright (C) 2006-2008 Adolfo González Blázquez <code@infinicode.org>

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

If you find any bugs or have any suggestions email: code@infinicode.org
"""

import os
import dircache
import glob
import re
import sys
import time
import random

import pyrenamer_globals

import EXIF

if pyrenamer_globals.have_hachoir:
    from pyrenamer_metadata import PyrenamerMetadataMusic

if pyrenamer_globals.have_eyed3:
    import eyeD3

from gettext import gettext as _

STOP = False

def set_stop(stop):
    """ Set stop var to see if ther's no need to keep reading files """
    global STOP
    STOP = stop


def get_stop():
    return STOP


def escape_pattern(pattern):
    """ Escape special chars on patterns, so glob doesn't get confused """
    pattern = pattern.replace('[', '[[]')
    return pattern


def get_file_listing(dir, mode, pattern=None):
    """ Returns the file listing of a given directory. It returns only files.
    Returns a list of [file,/path/to/file] """

    filelist = []

    if  pattern == (None or ''):
        listaux = dircache.listdir(dir)
    else:
        if dir != '/': dir += '/'
        dir = escape_pattern(dir + pattern)
        listaux = glob.glob(dir)

    listaux.sort(key=str.lower)
    for elem in listaux:
        if STOP: return filelist
        if mode == 0:
            # Get files
            if not os.path.isdir(os.path.join(dir,elem)):
                filelist.append([os.path.basename(elem),os.path.join(dir,elem)])
        elif mode == 1:
            # Get directories
            if os.path.isdir(os.path.join(dir,elem)):
                filelist.append([os.path.basename(elem),os.path.join(dir,elem)])
        elif mode == 2:
            # Get files and directories
            filelist.append([os.path.basename(elem),os.path.join(dir,elem)])
        else:
            # Get files
            if not os.path.isdir(os.path.join(dir,elem)):
                filelist.append([os.path.basename(elem),os.path.join(dir,elem)])

    return filelist


def get_file_listing_recursive(dir, mode, pattern=None):
    """ Returns the file listing of a given directory recursively.
    It returns only files. Returns a list of [file,/path/to/file] """

    filelist = []

    # Get subdirs
    for root, dirs, files in os.walk(dir, topdown=False):
        if STOP: return filelist
        for directory in dirs:
            if STOP: return filelist
            elem = get_file_listing(os.path.join(root, directory), mode, pattern)
            for i in elem:
                if STOP: return filelist
                filelist.append(i)

    # Get root directory files
    list = get_file_listing(dir, mode, pattern)
    for i in list:
        filelist.append(i)

    return filelist


def get_dir_listing(dir):
    """ Returns the subdirectory listing of a given directory. It returns only directories.
     Returns a list of [dir,/path/to/dir] """

    dirlist = []

    listaux = dircache.listdir(dir)
    listaux.sort(key=str.lower)
    for elem in listaux:
        if STOP: return dirlist
        if os.path.isdir(os.path.join(dir,elem)): dirlist.append([os.path.basename(elem),os.path.join(dir,elem)])

    return dirlist


def get_new_path(name, path):
    """ Remove file from path, so we have only the dir"""
    dirpath = os.path.split(path)[0]
    if dirpath != '/': dirpath += '/'
    return dirpath + name


def replace_spaces(name, path, mode):
    """ if mode == 0: ' ' -> '_'
        if mode == 1: '_' -> ' '
        if mode == 2: '_' -> '.'
        if mode == 3: '.' -> ' '
        if mode == 4: ' ' -> '-'
        if mode == 5: '-' -> ' ' """

    name = unicode(name)
    path = unicode(path)

    if mode == 0:
        newname = name.replace(' ', '_')
    elif mode == 1:
        newname = name.replace('_', ' ')
    elif mode == 2:
        newname = name.replace(' ', '.')
    elif mode == 3:
        newname = name.replace('.', ' ')
    elif mode == 4:
        newname = name.replace(' ', '-')
    elif mode == 5:
        newname = name.replace('-', ' ')

    newpath = get_new_path(newname, path)
    return unicode(newname), unicode(newpath)


def replace_capitalization(name, path, mode):
    """ 0: all to uppercase
    1: all to lowercase
    2: first letter uppercase
    3: first letter uppercase of each word """
    name = unicode(name)
    path = unicode(path)

    if mode == 0:
        newname = name.upper()
    elif mode == 1:
        newname = name.lower()
    elif mode == 2:
        newname = name.capitalize()
    elif mode == 3:
        #newname = name.title()
        newname = ' '.join([x.capitalize() for x in name.split()])

    newpath = get_new_path(newname, path)
    return unicode(newname), unicode(newpath)


def replace_with(name, path, orig, new):
    """ Replace all occurences of orig with new """
    newname = name.replace(orig, new)
    newpath = get_new_path(newname, path)

    return unicode(newname), unicode(newpath)


def replace_accents(name, path):
    """ Remove accents, umlauts and other locale symbols from words """
    name = unicode(name)
    path = unicode(path)

    newname = name.replace('á', 'a')
    newname = newname.replace('à', 'a')
    newname = newname.replace('ä', 'a')
    newname = newname.replace('â', 'a')
    newname = newname.replace('Á', 'A')
    newname = newname.replace('À', 'A')
    newname = newname.replace('Ä', 'A')
    newname = newname.replace('Â', 'A')

    newname = newname.replace('é', 'e')
    newname = newname.replace('è', 'e')
    newname = newname.replace('ë', 'e')
    newname = newname.replace('ê', 'e')
    newname = newname.replace('É', 'E')
    newname = newname.replace('È', 'E')
    newname = newname.replace('Ë', 'E')
    newname = newname.replace('Ê', 'E')

    newname = newname.replace('í', 'i')
    newname = newname.replace('ì', 'i')
    newname = newname.replace('ï', 'i')
    newname = newname.replace('î', 'i')
    newname = newname.replace('Í', 'I')
    newname = newname.replace('Ì', 'I')
    newname = newname.replace('Ï', 'I')
    newname = newname.replace('Î', 'I')

    newname = newname.replace('ó', 'o')
    newname = newname.replace('ò', 'o')
    newname = newname.replace('ö', 'o')
    newname = newname.replace('ô', 'o')
    newname = newname.replace('Ó', 'O')
    newname = newname.replace('Ò', 'O')
    newname = newname.replace('Ö', 'O')
    newname = newname.replace('Ô', 'O')

    newname = newname.replace('ú', 'u')
    newname = newname.replace('ù', 'u')
    newname = newname.replace('ü', 'u')
    newname = newname.replace('û', 'u')
    newname = newname.replace('Ú', 'U')
    newname = newname.replace('Ù', 'U')
    newname = newname.replace('Ü', 'U')
    newname = newname.replace('Û', 'U')

    """ Czech language accents replacement """
    newname = newname.replace('ě', 'e')
    newname = newname.replace('š', 's')
    newname = newname.replace('č', 'c')
    newname = newname.replace('ř', 'r')
    newname = newname.replace('ž', 'z')
    newname = newname.replace('ý', 'y')
    newname = newname.replace('ů', 'u')
    newname = newname.replace('Ě', 'E')
    newname = newname.replace('Š', 'S')
    newname = newname.replace('Č', 'C')
    newname = newname.replace('Ř', 'R')
    newname = newname.replace('Ž', 'Z')
    newname = newname.replace('Ý', 'Y')
    newname = newname.replace('Ů', 'U')

    newpath = get_new_path(newname, path)
    return unicode(newname), unicode(newpath)


def replace_duplicated(name, path):
    """ Remove duplicated symbols """

    name = unicode(name)
    path = unicode(path)

    symbols = ['.', ' ', '-', '_']

    newname = name[0]
    for c in name[1:]:
        if c in symbols:
            if newname[-1] != c:
                newname += c
        else:
            newname += c

    newpath = get_new_path(newname, path)
    return unicode(newname), unicode(newpath)


def rename_using_patterns(name, path, pattern_ini, pattern_end, count):
    """ This method parses te patterns given by the user and stores the new filename
    on the treestore. Posibble patterns are:

    {#} Numbers
    {L} Letters
    {C} Characters (Numbers & letters, not spaces)
    {X} Numbers, letters, and spaces
    {@} Trash
    """
    name = unicode(name)
    path = unicode(path)

    pattern = pattern_ini
    newname = pattern_end

    pattern = pattern.replace('.','\.')
    pattern = pattern.replace('[','\[')
    pattern = pattern.replace(']','\]')
    pattern = pattern.replace('(','\(')
    pattern = pattern.replace(')','\)')
    pattern = pattern.replace('?','\?')
    pattern = pattern.replace('{#}', '([0-9]*)')
    pattern = pattern.replace('{L}', '([a-zA-Z]*)')
    pattern = pattern.replace('{C}', '([\S]*)')
    pattern = pattern.replace('{X}', '([\S\s]*)')
    pattern = pattern.replace('{@}', '(.*)')

    repattern = re.compile(pattern)
    try:
        groups = repattern.search(name).groups()

        for i in range(len(groups)):
            newname = newname.replace('{'+`i+1`+'}',groups[i])
    except:
        return None, None

    # Replace {num} with item number.
    # If {num2} the number will be 02
    # If {num3+10} the number will be 010
    count = `count`
    cr = re.compile("{(num)([0-9]*)}"
                    "|{(num)([0-9]*)(\+)([0-9]*)}")
    try:
        cg = cr.search(newname).groups()
        if len(cg) == 6:

            if cg[0] == 'num':
                # {num2}
                if cg[1] != '': count = count.zfill(int(cg[1]))
                newname = cr.sub(count, newname)

            elif cg[2] == 'num' and cg[4] == '+':
                # {num2+5}
                if cg[5] != '': count = str(int(count)+int(cg[5]))
                if cg[3] != '': count = count.zfill(int(cg[3]))

        newname = cr.sub(count, newname)
    except:
        pass

    # Replace {dir} with directory name
    dir = os.path.dirname(path)
    dir = os.path.basename(dir)
    newname = newname.replace('{dir}', dir)

    # Some date replacements
    newname = newname.replace('{date}', time.strftime("%d%b%Y", time.localtime()))
    newname = newname.replace('{year}', time.strftime("%Y", time.localtime()))
    newname = newname.replace('{month}', time.strftime("%m", time.localtime()))
    newname = newname.replace('{monthname}', time.strftime("%B", time.localtime()))
    newname = newname.replace('{monthsimp}', time.strftime("%b", time.localtime()))
    newname = newname.replace('{day}', time.strftime("%d", time.localtime()))
    newname = newname.replace('{dayname}', time.strftime("%A", time.localtime()))
    newname = newname.replace('{daysimp}', time.strftime("%a", time.localtime()))

    # Replace {rand} with random number between 0 and 100.
    # If {rand500} the number will be between 0 and 500
    # If {rand10-20} the number will be between 10 and 20
    # If you add ,5 the number will be padded with 5 digits
    # ie. {rand20,5} will be a number between 0 and 20 of 5 digits (00012)
    rnd = ''
    cr = re.compile("{(rand)([0-9]*)}"
                    "|{(rand)([0-9]*)(\-)([0-9]*)}"
                    "|{(rand)([0-9]*)(\,)([0-9]*)}"
                    "|{(rand)([0-9]*)(\-)([0-9]*)(\,)([0-9]*)}")
    try:
        cg = cr.search(newname).groups()
        if len(cg) == 16:

            if cg[0] == 'rand':
                if cg[1] == '':
                    # {rand}
                    rnd = random.randint(0,100)
                else:
                    # {rand2}
                    rnd = random.randint(0,int(cg[1]))

            elif cg[2] == 'rand' and cg[4] == '-' and cg[3] != '' and cg[5] != '':
                # {rand10-100}
                rnd = random.randint(int(cg[3]),int(cg[5]))

            elif cg[6] == 'rand' and cg[8] == ',' and cg[9] != '':
                if cg[7] == '':
                    # {rand,2}
                    rnd = str(random.randint(0,100)).zfill(int(cg[9]))
                else:
                    # {rand10,2}
                    rnd = str(random.randint(0,int(cg[7]))).zfill(int(cg[9]))

            elif cg[10] == 'rand' and cg[12] == '-' and cg[14] == ',' and cg[11] != '' and cg[13] != '' and cg[15] != '':
                # {rand2-10,3}
                rnd = str(random.randint(int(cg[11]),int(cg[13]))).zfill(int(cg[15]))

        newname = cr.sub(str(rnd), newname)
    except:
        pass

    # Returns new name and path
    newpath = get_new_path(newname, path)
    return unicode(newname), unicode(newpath)


def replace_images(name, path, newname, newpath):
    """ Pattern replace for images """

    name = unicode(name)
    path = unicode(path)
    newname = unicode(newname)
    newpath = unicode(newpath)

    # Image EXIF replacements
    date, width, height, cameramaker, cameramodel = get_exif_data(get_new_path(name, path))

    if date != None:
        newname = newname.replace('{imagedate}', time.strftime("%d%b%Y", date))
        newname = newname.replace('{imageyear}', time.strftime("%Y", date))
        newname = newname.replace('{imagemonth}', time.strftime("%m", date))
        newname = newname.replace('{imagemonthname}', time.strftime("%B", date))
        newname = newname.replace('{imagemonthsimp}', time.strftime("%b", date))
        newname = newname.replace('{imageday}', time.strftime("%d", date))
        newname = newname.replace('{imagedayname}', time.strftime("%A", date))
        newname = newname.replace('{imagedaysimp}', time.strftime("%a", date))
        newname = newname.replace('{imagetime}', time.strftime("%H_%M_%S", date))
        newname = newname.replace('{imagehour}', time.strftime("%H", date))
        newname = newname.replace('{imageminute}', time.strftime("%M", date))
        newname = newname.replace('{imagesecond}', time.strftime("%S", date))
    else:
        newname = newname.replace('{imagedate}','')
        newname = newname.replace('{imageyear}', '')
        newname = newname.replace('{imagemonth}', '')
        newname = newname.replace('{imagemonthname}', '')
        newname = newname.replace('{imagemonthsimp}', '')
        newname = newname.replace('{imageday}', '')
        newname = newname.replace('{imagedayname}', '')
        newname = newname.replace('{imagedaysimp}', '')
        newname = newname.replace('{imagetime}', '')
        newname = newname.replace('{imagehour}', '')
        newname = newname.replace('{imageminute}', '')
        newname = newname.replace('{imagesecond}', '')

    if width != None: newname = newname.replace('{imagewidth}', width)
    else: newname = newname.replace('{imagewidth}', '')

    if height != None: newname = newname.replace('{imageheight}', height)
    else: newname = newname.replace('{imageheight}', '')

    if cameramaker != None: newname = newname.replace('{cameramaker}', cameramaker)
    else: newname = newname.replace('{cameramaker}', '')

    if cameramodel != None: newname = newname.replace('{cameramodel}', cameramodel)
    else: newname = newname.replace('{cameramodel}', '')

    # Returns new name and path
    newpath = get_new_path(newname, path)
    return unicode(newname), unicode(newpath)


def get_exif_data(path):
    """ Get EXIF data from file. """
    date = None
    width = None
    height = None
    cameramaker = None
    cameramodel = None

    try:
        file = open(path, 'rb')
    except:
        print "ERROR: Opening image file", path
        return date, width, height, cameramaker, cameramodel

    try:
        tags = EXIF.process_file(file)
        if not tags:
            print "ERROR: No EXIF tags on", path
            return date, width, height, cameramaker, cameramodel
    except:
        print "ERROR: proccesing EXIF tags on", path
        return date, width, height, cameramaker, cameramodel

    # tags['EXIF DateTimeOriginal'] = "2001:03:31 12:27:36"
    if tags.has_key('EXIF DateTimeOriginal'):
        data = str(tags['EXIF DateTimeOriginal'])
        try:
            date = time.strptime(data, "%Y:%m:%d %H:%M:%S")
        except:
            date = None

    if tags.has_key('EXIF ExifImageWidth'):
        width = str(tags['EXIF ExifImageWidth'])

    if tags.has_key('EXIF ExifImageLength'):
        height = str(tags['EXIF ExifImageLength'])

    if tags.has_key('Image Make'):
        cameramaker = str(tags['Image Make'])

    if tags.has_key('Image Model'):
        cameramodel = str(tags['Image Model'])

    return date, width, height, cameramaker, cameramodel


def replace_music_hachoir(name, path, newname, newpath):
    """ Pattern replace for music """

    file = get_new_path(name, path)

    try:
        tags = PyrenamerMetadataMusic(file)

        artist = clean_metadata(tags.get_artist())
        album  = clean_metadata(tags.get_album())
        title  = clean_metadata(tags.get_title())
        track  = clean_metadata(tags.get_track_number())
        trackt = clean_metadata(tags.get_track_total())
        genre  = clean_metadata(tags.get_genre())
        year   = clean_metadata(tags.get_year())

        if artist != None: newname = newname.replace('{artist}', artist)
        else: newname = newname.replace('{artist}', '')

        if album != None: newname = newname.replace('{album}', album)
        else: newname = newname.replace('{album}', '')

        if title != None: newname = newname.replace('{title}', title)
        else: newname = newname.replace('{title}', '')

        if track != None: newname = newname.replace('{track}', str(track).zfill(2))
        else: newname = newname.replace('{track}', '')

        if trackt != None: newname = newname.replace('{tracktotal}', str(trackt).zfill(2))
        else: newname = newname.replace('{tracktotal}', '')

        if genre != None: newname = newname.replace('{genre}', genre)
        else: newname = newname.replace('{genre}', '')

        if year != None: newname = newname.replace('{myear}', year)
        else: newname = newname.replace('{myear}', '')

    except:
        newname = newname.replace('{artist}', '')
        newname = newname.replace('{album}', '')
        newname = newname.replace('{title}', '')
        newname = newname.replace('{track}', '')
        newname = newname.replace('{tracktotal}', '')
        newname = newname.replace('{genre}', '')
        newname = newname.replace('{myear}', '')

    # Returns new name and path
    newpath = get_new_path(newname, path)
    return unicode(newname), unicode(newpath)

def replace_music_eyed3(name, path, newname, newpath):
    """ Pattern replace for mp3 """

    file = get_new_path(name, path)

    if eyeD3.isMp3File(file):
        try:
            audioFile = eyeD3.Mp3AudioFile(file, eyeD3.ID3_ANY_VERSION)
            tag = audioFile.getTag()
        except Exception, e:
            print "ERROR eyeD3:", e
            newpath = get_new_path('', path)
            return '', unicode(newpath)

        try:
            artist = clean_metadata(tag.getArtist())
        except Exception, e:
            print "ERROR eyeD3:", e
            artist = None

        try:
            album  = clean_metadata(tag.getAlbum())
        except Exception, e:
            print "ERROR eyeD3:", e
            album = None

        try:
            title  = clean_metadata(tag.getTitle())
        except Exception, e:
            print "ERROR eyeD3:", e
            title = None

        try:
            track  = clean_metadata(tag.getTrackNum()[0])
        except Exception, e:
            print "ERROR eyeD3:", e
            track = None

        try:
            trackt = clean_metadata(tag.getTrackNum()[1])
        except Exception, e:
            print "ERROR eyeD3:", e
            trackt = None

        try:
            genre  = clean_metadata(tag.getGenre().getName())
        except Exception, e:
            print "ERROR eyeD3:", e
            genre = None

        try:
            year   = clean_metadata(tag.getYear())
        except Exception, e:
            print "ERROR eyeD3:", e
            year = None

        if artist != None: newname = newname.replace('{artist}', artist)
        else: newname = newname.replace('{artist}', '')

        if album != None: newname = newname.replace('{album}', album)
        else: newname = newname.replace('{album}', '')

        if title != None: newname = newname.replace('{title}', title)
        else: newname = newname.replace('{title}', '')

        if track != None: newname = newname.replace('{track}', str(track))
        else: newname = newname.replace('{track}', '')

        if trackt != None: newname = newname.replace('{tracktotal}', str(trackt))
        else: newname = newname.replace('{tracktotal}', '')

        if genre != None: newname = newname.replace('{genre}', genre)
        else: newname = newname.replace('{genre}', '')

        if year != None: newname = newname.replace('{myear}', year)
        else: newname = newname.replace('{myear}', '')
    else:
        newname = newname.replace('{artist}', '')
        newname = newname.replace('{album}', '')
        newname = newname.replace('{title}', '')
        newname = newname.replace('{track}', '')
        newname = newname.replace('{tracktotal}', '')
        newname = newname.replace('{genre}', '')
        newname = newname.replace('{myear}', '')

    # Returns new name and path
    newpath = get_new_path(newname, path)
    return unicode(newname), unicode(newpath)


def rename_file(ori, new):
    """ Change filename with the new one """

    if ori == new:
        return True, None    # We don't need to rename the file, but don't show error message

    if os.path.exists(new):
        print _("Error while renaming %s to %s! -> %s already exists!") % (ori, new, new)
        error = "[Errno 17] %s" % os.strerror(17)
        return False, error

    try:
        os.renames(ori, new)
        print "Renaming %s to %s" % (ori, new)
        return True, None
    except Exception, e:
        print _("Error while renaming %s to %s!") % (ori, new)
        print e
        return False, e


def insert_at(name, path, text, pos):
    """ Append text at given position"""
    if pos >= 0:
        ini = name[0:pos]
        end = name[pos:len(name)]
        newname = ini + text + end
    else:
        newname = name + text

    newpath = get_new_path(newname, path)
    return unicode(newname), unicode(newpath)


def delete_from(name, path, ini, to, end):
    """ Delete chars from ini till to"""

    inin = ini
    ton  = to

    if end:
        ini = len(name) -1 - ton
        to  = len(name) -1 - inin
        if ini < 0: ini = 0

    textini = name[0:ini]
    textend = name[to+1:len(name)]
    newname = textini + textend

    newpath = get_new_path(newname, path)
    return unicode(newname), unicode(newpath)

def cut_extension(name, path):
    """ Remove extension from file name """

    if '.' in name:
        ext = name.split('.')[-1]
        name = name[0:len(name)-len(ext)-1]
        path = path[0:len(path)-len(ext)-1]
        return name, path, ext
    else:
        return name, path, ''

def add_extension(name, path, ext):
    """ Add extension to file name """

    if ext != '' and ext != None and name != '' and name != None:
        name = name + '.' + ext
        path = path + '.' + ext
    return name, path


def clean_metadata(tag):
    """ Removes reserver characters from a given filename """
    try:
        tag = tag.replace('|', '')
        tag = tag.replace('/', '')
        tag = tag.replace('\\', '')
        tag = tag.replace('?', '')
        tag = tag.replace('%', '')
        tag = tag.replace('*', '')
        tag = tag.replace(':', '')
        tag = tag.replace('<', '')
        tag = tag.replace('>', '')
        tag = tag.replace('"', '')
        return tag
    except:
        return None