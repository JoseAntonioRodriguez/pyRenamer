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

from hachoir_core.cmd_line import unicodeFilename
from hachoir_parser import createParser
from hachoir_metadata import extractMetadata
from hachoir_metadata.metadata import MultipleMetadata

class PyrenamerMetadataException(Exception):
       def __init__(self, value):
           self.parameter = value
       def __str__(self):
           return repr(self.parameter)

class PyrenamerMetadata(PyrenamerMetadataException):

    def __init__(self,  name):
        self.real_filename = name
        self.filename = unicodeFilename(self.real_filename)
        self.parser = createParser(self.filename, real_filename=self.real_filename)

    def get_mime_type(self):
        return self.parser.mime_type

    def get_metadata(self):
        self.metadata = extractMetadata(self.parser)


class PyrenamerMetadataMusic(PyrenamerMetadata):

    def __init__(self, name):
        super(PyrenamerMetadataMusic, self).__init__(name)

        if not 'audio' in self.parser.mime_type:
            raise PyrenamerMetadataException("File is not music!")

        self.get_metadata()
        if self.metadata is None:
            raise PyrenamerMetadataException("No metadata in file!")
        else:
            self.parse_metadata()

    def parse_metadata(self):
        self.tags = {}
        for data in sorted(self.metadata):
            if not data.values:
                continue
            title = data.description
            value = ''
            for item in data.values:
                value += item.text
            self.tags[title] = value

    def get_artist(self):
        try:
            return self.tags["Artist"]
        except:
            try:
                return self.tags["Author"]
            except:
                return None

    def get_album(self):
        try:
            return self.tags["Album"]
        except:
            return None

    def get_title(self):
        try:
            return self.tags["Title"]
        except:
            return None

    def get_track_number(self):
        try:
            return self.tags["Track number"]
        except:
            return None

    def get_track_total(self):
        try:
            return self.tags["Track total"]
        except:
            return None

    def get_genre(self):
        try:
            return self.tags["Music genre"]
        except:
            return None

    def get_year(self):
        try:
            return self.tags["Creation date"]
        except:
            return None

    def get_duration(self):
        try:
            return self.tags["Duration"]
        except:
            return None

    def get_bitrate(self):
        try:
            return self.tags["Bit rate"]
        except:
            return None
