# Copyright (C) 2006-2007 Adolfo González Blázquez <code@infinicode.org>
# Copyright (C) 2022 Jose Antonio Rodríguez Fernández <joseantonio.rguez.fdez@gmail.com>
#
# This file is part of pyRenamer.
#
# pyRenamer is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyRenamer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyRenamer. If not, see <https://www.gnu.org/licenses/>.


from abc import ABC, abstractmethod
import os.path
import unicodedata
import re
import time
import random
from contextlib import suppress

from gi.repository import GLib, GExiv2
import taglib


class _RenamingRule(ABC):
    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def reset(self): ...

    def rename(self, path, keep_extension=False):
        dirname, name = os.path.split(path)
        name, ext = os.path.splitext(name) if keep_extension else (name, '')
        return os.path.join(dirname, self._rename_name(name, dirname, path) + ext)

    @abstractmethod
    def _rename_name(self, name, dirname, path): ...



class RenamingRulePattern(_RenamingRule):
    DEFAULT_MIN_RANDOM = 0
    DEFAULT_MAX_RANDOM = 100

    def __init__(self, original_pattern, renamed_pattern):
        super().__init__()
        self._original_pattern = original_pattern
        self._renamed_pattern = renamed_pattern
        self._count = 0

    def __repr__(self):
        return (f"<{self.__class__.__name__} "
                f"original_pattern='{self._original_pattern}', renamed_pattern='{self._renamed_pattern}'>")

    def reset(self):
        self._count = 0

    def _rename_name(self, name, dirname, path):
        new_name = self._replace_regex(name)
        new_name = self._replace_num(new_name)
        new_name = self._replace_dir(new_name, dirname)
        new_name = self._replace_date(new_name)
        new_name = self._replace_rand(new_name)
        return new_name

    def _replace_regex(self, name):
        new_name = self._renamed_pattern

        pattern = re.escape(self._original_pattern)
        pattern = pattern.replace('\{\#\}', '([\d]+)')
        pattern = pattern.replace('\{L\}', '([a-zA-Z]+)')
        pattern = pattern.replace('\{C\}', '([\S]+)')
        pattern = pattern.replace('\{X\}', '([\S\s]+)')
        pattern = pattern.replace('\{@\}', '(.+)')

        match = re.search(pattern, name)
        if not match:
            return name

        groups = match.groups()
        for i, group in enumerate(groups):
            new_name = new_name.replace(f'{{{i + 1}}}', group)

        return new_name

    def _get_count(self, match):
        count = self._count
        inc = match.group('inc')
        if inc:
            count += int(inc)
        zfill = match.group('zfill')
        if zfill:
            count = str(count).zfill(int(zfill))
        return str(count)

    def _replace_num(self, name):
        # Replace {num} with count
        # If {num2} the number will be 02
        # If {num3+10} the number will be 010
        pattern = r'\{num(?P<zfill>\d+)?(?:\+(?P<inc>\d+))?\}'
        new_name = re.sub(pattern, self._get_count, name)
        self._count += 1
        return new_name

    def _replace_dir(self, name, dirname):
        # Replace {dir} with directory name
        return name.replace('{dir}', os.path.basename(dirname))

    def _replace_date(self, name):
        # Date replacements
        current_time = time.localtime()
        return name \
            .replace('{date}', time.strftime('%d%b%Y', current_time)) \
            .replace('{year}', time.strftime('%Y', current_time)) \
            .replace('{month}', time.strftime('%m', current_time)) \
            .replace('{monthname}', time.strftime('%B', current_time)) \
            .replace('{monthsimp}', time.strftime('%b', current_time)) \
            .replace('{day}', time.strftime('%d', current_time)) \
            .replace('{dayname}', time.strftime('%A', current_time)) \
            .replace('{daysimp}', time.strftime('%a', current_time))

    def _get_random(self, match):
        start = match.group('start')
        start = int(start) if start is not None else self.DEFAULT_MIN_RANDOM
        end = match.group('end')
        end = int(end) if end is not None else self.DEFAULT_MAX_RANDOM
        end = max(start, end)
        number = random.randint(start, end)
        zfill = match.group('zfill')
        if zfill:
            number = str(number).zfill(int(zfill))
        return str(number)

    def _replace_rand(self, name):
        # Replace {rand} with a random number between 0 and 100
        # If {rand500} the number will be between 0 and 500
        # If {rand10-20} the number will be between 10 and 20
        # If you add ,5 the number will be padded with 5 digits
        # ie. {rand20,5} will be a number between 0 and 20 of 5 digits (00012)
        pattern = r'\{rand(?:(?:(?P<start>\d+)-)?(?P<end>\d+))?(?:,(?P<zfill>\d+))?\}'
        return re.sub(pattern, self._get_random, name)


class RenamingRulePatternImages(RenamingRulePattern):
    def __init__(self, original_pattern, renamed_pattern):
        super().__init__(original_pattern, renamed_pattern)

    def __repr__(self):
        return (f"<{self.__class__.__name__} "
                f"original_pattern='{self._original_pattern}', renamed_pattern='{self._renamed_pattern}'>")

    def _rename_name(self, name, dirname, path):
        new_name = super()._rename_name(name, dirname, path)
        new_name = self._replace_image_tags(new_name, path)
        return new_name

    def _replace_image_tags(self, name, path):
        width = ''
        height = ''
        date = None
        maker = ''
        model = ''

        with suppress(GLib.Error):
            exif = GExiv2.Metadata(path)
            width = str(exif.get_pixel_width())
            height = str(exif.get_pixel_height())
            if exif.has_tag('Exif.Photo.DateTimeOriginal'):
                with suppress(ValueError):
                    date = time.strptime(exif.get_tag_string('Exif.Photo.DateTimeOriginal'), '%Y:%m:%d %H:%M:%S')
            if exif.has_tag('Exif.Image.Make'):
                maker = exif.get_tag_string('Exif.Image.Make')
            if exif.has_tag('Exif.Image.Model'):
                model = exif.get_tag_string('Exif.Image.Model')

        return name \
            .replace('{imagewidth}', width) \
            .replace('{imageheight}', height) \
            .replace('{cameramaker}', maker) \
            .replace('{cameramodel}', model) \
            .replace('{imagedate}', time.strftime('%d%b%Y', date) if date else '') \
            .replace('{imageyear}', time.strftime('%Y', date) if date else '') \
            .replace('{imagemonth}', time.strftime('%m', date) if date else '') \
            .replace('{imagemonthname}', time.strftime('%B', date) if date else '') \
            .replace('{imagemonthsimp}', time.strftime('%b', date) if date else '') \
            .replace('{imageday}', time.strftime('%d', date) if date else '') \
            .replace('{imagedayname}', time.strftime('%A', date) if date else '') \
            .replace('{imagedaysimp}', time.strftime('%a', date) if date else '') \
            .replace('{imagetime}', time.strftime('%H_%M_%S', date) if date else '') \
            .replace('{imagehour}', time.strftime('%H', date) if date else '') \
            .replace('{imageminute}', time.strftime('%M', date) if date else '') \
            .replace('{imagesecond}', time.strftime('%S', date) if date else '')


class RenamingRulePatternMusic(RenamingRulePattern):
    def __init__(self, original_pattern, renamed_pattern):
        super().__init__(original_pattern, renamed_pattern)

    def __repr__(self):
        return (f"<{self.__class__.__name__} "
                f"original_pattern='{self._original_pattern}', renamed_pattern='{self._renamed_pattern}'>")

    def _rename_name(self, name, dirname, path):
        new_name = super()._rename_name(name, dirname, path)
        new_name = self._replace_music_tags(new_name, path)
        return new_name

    def _replace_music_tags(self, name, path):
        artist = ''
        album = ''
        title = ''
        genre = ''
        year = ''
        track = ''
        track_total = ''

        with suppress(OSError):
            tags = taglib.File(path).tags
            if 'ARTIST' in tags:
                artist = tags['ARTIST'][0]
            if 'ALBUM' in tags:
                album = tags['ALBUM'][0]
            if 'TITLE' in tags:
                title = tags['TITLE'][0]
            if 'GENRE' in tags:
                genre = tags['GENRE'][0]
            if 'DATE' in tags:
                year = tags['DATE'][0]
            if 'TRACKNUMBER' in tags:
                track_number = tags['TRACKNUMBER'][0]
                if '/' in track_number:
                    track, track_total = track_number.split('/')
                else:
                    track = track_number

        return name \
            .replace('{artist}', artist) \
            .replace('{album}', album) \
            .replace('{title}', title) \
            .replace('{track}', track) \
            .replace('{tracktotal}', track_total) \
            .replace('{genre}', genre) \
            .replace('{myear}', year)


class RenamingRuleSpaces(_RenamingRule):
    def __init__(self, mode):
        super().__init__()
        self._mode = mode

    def __repr__(self):
        return f"<{self.__class__.__name__} mode={self._mode}>"

    def _rename_name(self, name, dirname, path):
        if self._mode == 'spaces-to-underscores':
            return name.replace(' ', '_')
        if self._mode == 'underscores-to-spaces':
            return name.replace('_', ' ')
        if self._mode == 'spaces-to-dots':
            return name.replace(' ', '.')
        if self._mode == 'dots-to-spaces':
            return name.replace('.', ' ')
        if self._mode == 'spaces-to-hyphens':
            return name.replace(' ', '-')
        if self._mode == 'hyphens-to-spaces':
            return name.replace('-', ' ')
        return name


class RenamingRuleReplace(_RenamingRule):
    def __init__(self, old, new):
        super().__init__()
        self._old = old
        self._new = new

    def __repr__(self):
        return f"<{self.__class__.__name__} old='{self._old}', new='{self._new}'>"

    def _rename_name(self, name, dirname, path):
        return name.replace(self._old, self._new)


class RenamingRuleCapitalization(_RenamingRule):
    def __init__(self, mode):
        super().__init__()
        self._mode = mode

    def __repr__(self):
        return f"<{self.__class__.__name__} mode={self._mode}>"

    def _rename_name(self, name, dirname, path):
        if self._mode == 'uppercase':
            return name.upper()
        if self._mode == 'lowercase':
            return name.lower()
        if self._mode == 'sentence-case':
            return name.capitalize()
        if self._mode == 'title-case':
            return ' '.join(word.capitalize() for word in name.split(' '))
        return name


class RenamingRuleRemoveAccents(_RenamingRule):
    def _rename_name(self, name, dirname, path):
        return ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')


class RenamingRuleFixDuplicated(_RenamingRule):
    def _rename_name(self, name, dirname, path):
        return re.sub(r'([. _-])\1+', r'\1', name)


class RenamingRuleInsert(_RenamingRule):
    def __init__(self, text, at=0, at_the_end=False):
        super().__init__()
        self._text = text
        self._at = at
        self._at_the_end = at_the_end

    def __repr__(self):
        return f"<{self.__class__.__name__} text='{self._text}', at={self._at}, at_the_end={self._at_the_end}>"

    def _rename_name(self, name, dirname, path):
        if self._at_the_end:
            return name + self._text
        else:
            return name[:self._at] + self._text + name[self._at:]


class RenamingRuleDelete(_RenamingRule):
    def __init__(self, from_, to, from_the_end=False):
        super().__init__()
        self._from = from_
        self._to = to
        self._from_the_end = from_the_end

    def __repr__(self):
        return f"<{self.__class__.__name__} from={self._from}, to={self._to}, from_the_end={self._from_the_end}>"

    @staticmethod
    def _reversed(string):
        return string[::-1]

    @staticmethod
    def _delete_chars(string, from_, to):
        return string[:from_] + string[to + 1:]

    def _rename_name(self, name, dirname, path):
        if not self._from_the_end:
            return self._delete_chars(name, self._from, self._to)
        else:
            return self._reversed(self._delete_chars(self._reversed(name), self._from, self._to))


class RenamingRuleManual(_RenamingRule):
    def __init__(self, new_name):
        super().__init__()
        self._new_name = new_name

    def __repr__(self):
        return f"<{self.__class__.__name__} new_name='{self._new_name}'>"

    def _rename_name(self, name, dirname, path):
        return self._new_name or name
