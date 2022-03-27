#! /bin/sh

VERSION=`cat configure.ac | grep AC_INIT | grep -o "[0-9]\.[0-9]\.[0-9]"`

if [ ! -d /usr/share/build-essential ]; then
	echo "Please install build-essential package!"
	exit 1
fi

if [ ! -f /usr/bin/dch ]; then
	echo "Please install devscripts package!"
	exit 1
fi

if [ ! -f /usr/bin/fakeroot ]; then
	echo "Please install fakeroot package!"
	exit 1
fi

sh autogen.sh

mkdir deb
cp debian/changelog debian.changelog

dch --newversion $VERSION+svn`date +%G%m%d%H%S`-1 "New version from SVN"
dpkg-buildpackage -rfakeroot -us -uc

mv ../pyrenamer_$VERSION+svn* deb/

if [ -d ~/pyrenamer-deb ]; then
	mv deb/* ~/pyrenamer-deb
	rmdir deb/
else
	mv deb/ ~/pyrenamer-deb
fi

rm debian/changelog
mv debian.changelog debian/changelog

fakeroot ./debian/rules clean

echo
echo
echo "Files created on $HOME/pyrenamer-deb:"
ls ~/pyrenamer-deb
