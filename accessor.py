#!/usr/bin/env python
# Copyright (c) 2011 Citrix Systems, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation; version 2.1 only. with the special
# exception on linking described in file LICENSE.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.

"""accessor - provide common interface to access methods"""

import ftplib
import os
import socket
import sys
import tempfile
import types
import urllib
import urllib2
import urlparse

import xcp.mount as mount
import xcp.logger as logger

class SplitResult(object):
    def __init__(self, args):
        (
            self.scheme,
            self.netloc,
            self.path,
            _,
            __
        ) = args

    @property
    def username(self):
        netloc = self.netloc
        if "@" in netloc:
            userinfo = netloc.rsplit("@", 1)[0]
            if ":" in userinfo:
                userinfo = userinfo.split(":", 1)[0]
            return userinfo
        return None

    @property
    def password(self):
        netloc = self.netloc
        if "@" in netloc:
            userinfo = netloc.rsplit("@", 1)[0]
            if ":" in userinfo:
                return userinfo.split(":", 1)[1]
        return None

    @property
    def hostname(self):
        netloc = self.netloc
        if "@" in netloc:
            netloc = netloc.rsplit("@", 1)[1]
        if ":" in netloc:
            netloc = netloc.split(":", 1)[0]
        return netloc.lower() or None

def compat_urlsplit(url, allow_fragments = True):
    ret = urlparse.urlsplit(url, allow_fragments = allow_fragments)
    if 'SplitResult' in dir(urlparse):
        return ret
    return SplitResult(ret)

class Accessor(object):

    def __init__(self, ro):
        self.read_only = ro;

    def access(self, name):
        """ Return boolean determining where 'name' is an accessible object
        in the target. """
        try:
            f = self.openAddress(name)
            f.close()
        except Exception:
            return False

        return True

    def openAddress(self, name):
        """should be overloaded"""
        pass

    def canEject(self):
        return False

    def start(self):
        pass

    def finish(self):
        pass

    @staticmethod
    def _writeFile(in_fh, out_fh):
        while out_fh:
            data = in_fh.read(256 * 512)
            if len(data) == 0:
                break
            out_fh.write(data)
        out_fh.close()
        return True
    
class FilesystemAccessor(Accessor):
    def __init__(self, location, ro):
        super(FilesystemAccessor, self).__init__(ro)
        self.location = location

    def openAddress(self, addr):
        return open(os.path.join(self.location, addr), 'r')

class MountingAccessor(FilesystemAccessor):
    def __init__(self, mount_types, mount_source, mount_options = None):
        ro = isinstance(mount_options, types.ListType) and 'ro' in mount_options
        super(MountingAccessor, self).__init__(None, ro)

        self.mount_types = mount_types
        self.mount_source = mount_source
        self.mount_options = mount_options
        self.start_count = 0

    def start(self):
        if self.start_count == 0:
            self.location = tempfile.mkdtemp(prefix="media-", dir="/tmp")
            # try each filesystem in turn:
            success = False
            for fs in self.mount_types:
                try:
                    opts = self.mount_options
                    if fs == 'iso9660':
                        if isinstance(opts, types.ListType):
                            if 'ro' not in opts:
                                opts.append('ro')
                        else:
                            opts = ['ro']
                    mount.mount(self.mount_source, self.location,
                                options = opts,
                                fstype = fs)
                except mount.MountException:
                    continue
                else:
                    success = True
                    break
            if not success:
                os.rmdir(self.location)
                raise mount.MountException
        self.start_count += 1

    def finish(self):
        if self.start_count == 0:
            return
        self.start_count -= 1
        if self.start_count == 0:
            mount.umount(self.location)
            os.rmdir(self.location)
            self.location = None

    def writeFile(self, in_fh, out_name):
        logger.info("Copying to %s" % os.path.join(self.location, out_name))
        out_fh = open(os.path.join(self.location, out_name), 'w')
        return self._writeFile(in_fh, out_fh)

    def __del__(self):
        while self.start_count > 0:
            self.finish()

class DeviceAccessor(MountingAccessor):
    def __init__(self, device, ro, fs = None):
        """ Return a MountingAccessor for a device 'device', which should
        be a fully qualified path to a device node. """
        if device.startswith('dev://'):
            device = device[6:]
        if fs is None:
            fs = ['iso9660', 'vfat', 'ext3']
        opts = None
        if ro:
            opts = ['ro']
        super(DeviceAccessor, self).__init__(fs, device, opts)
        self.device = device

    def __repr__(self):
        return "<DeviceAccessor: %s>" % self.device

#    def canEject(self):
#        return diskutil.removable(self.device):

#    def eject(self):
#        assert self.canEject()
#        self.finish()
#        util.runCmd2(['/usr/bin/eject', self.device])

class NFSAccessor(MountingAccessor):
    def __init__(self, nfspath, ro):
        if nfspath.startswith('nfs://'):
            nfspath = nfspath[6:]
        opts = ['tcp']
        if ro:
            opts.append('ro')
        super(NFSAccessor, self).__init__(['nfs'], nfspath, opts)
        self.nfspath = nfspath

    def __repr__(self):
        return "<NFSAccessor: %s>" % self.nfspath

class FileAccessor(Accessor):
    def __init__(self, baseAddress, ro):
        if baseAddress.startswith('file://'):
            baseAddress = baseAddress[7:]
        assert baseAddress.endswith('/')
        super(FileAccessor, self).__init__(ro)
        self.baseAddress = baseAddress

    def openAddress(self, address):
        return open(os.path.join(self.baseAddress, address))

    def writeFile(self, in_fh, out_name):
        logger.info("Copying to %s" % os.path.join(self.baseAddress, out_name))
        out_fh = open(os.path.join(self.baseAddress, out_name), 'w')
        return self._writeFile(in_fh, out_fh)

    def __repr__(self):
        return "<FileAccessor: %s>" % self.baseAddress

class FTPAccessor(Accessor):
    def __init__(self, baseAddress, ro):
        super(FTPAccessor, self).__init__(ro)
        assert baseAddress.endswith('/')
        self.url_parts = compat_urlsplit(baseAddress, allow_fragments = False)
        self.baseAddress = baseAddress
        self.start_count = 0
        self.cleanup = False

    def _cleanup(self):
        if self.cleanup:
            # clean up after RETR
            self.ftp.voidresp()
            self.cleanup = False

    def start(self):
        if self.start_count == 0:
            self.ftp = ftplib.FTP(self.url_parts.hostname)
            #self.ftp.set_debuglevel(1)
            username = self.url_parts.username
            password = self.url_parts.password
            if username:
                username = urllib.unquote(username)
            if password:
                password = urllib.unquote(password)
            self.ftp.login(username, password)

            directory = urllib.unquote(self.url_parts.path[1:])
            if directory != '':
                logger.debug("Changing to " + directory)
                self.ftp.cwd(directory)

        self.start_count += 1

    def finish(self):
        if self.start_count == 0:
            return
        self.start_count -= 1
        if self.start_count == 0:
            self.ftp.quit()
            self.ftp = None

    def access(self, path):
        try:
            logger.debug("Testing "+path)
            self._cleanup()
            url = urllib.unquote(path)

            lst = self.ftp.nlst(os.path.dirname(url))
            return url in lst
        except Exception, e:
            logger.info(str(e))
            return False

    def openAddress(self, address):
        logger.debug("Opening "+address)
        self._cleanup()
        url = urllib.unquote(address)

        self.ftp.voidcmd('TYPE I')
        s = self.ftp.transfercmd('RETR ' + url).makefile('rb')
        self.cleanup = True
        return s

    def writeFile(self, in_fh, out_name):
        self._cleanup()
        fname = urllib.unquote(out_name)

        logger.debug("Storing as " + fname)
        self.ftp.storbinary('STOR ' + fname, in_fh)

    def __repr__(self):
        return "<FTPAccessor: %s>" % self.baseAddress

class HTTPAccessor(Accessor):
    def __init__(self, baseAddress, ro):
        assert baseAddress.endswith('/')
        assert ro
        super(HTTPAccessor, self).__init__(ro)
        self.url_parts = compat_urlsplit(baseAddress, allow_fragments = False)

        if self.url_parts.username:
            self.passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
            self.passman.add_password(None, self.url_parts.hostname,
                                      urllib.unquote(self.url_parts.username),
                                      urllib.unquote(self.url_parts.password))
            self.authhandler = urllib2.HTTPBasicAuthHandler(self.passman)
            self.opener = urllib2.build_opener(self.authhandler)
            urllib2.install_opener(self.opener)
        # rebuild URL without auth components
        self.baseAddress = urlparse.urlunsplit(
            (self.url_parts.scheme, self.url_parts.hostname,
             self.url_parts.path, '', ''))

    def openAddress(self, address):
        return urllib2.urlopen(os.path.join(self.baseAddress, address))

    def __repr__(self):
        return "<HTTPAccessor: %s>" % self.baseAddress

SUPPORTED_ACCESSORS = {'nfs': NFSAccessor,
                       'http': HTTPAccessor,
                       'https': HTTPAccessor,
                       'ftp': FTPAccessor,
                       'file': FileAccessor,
                       'dev': DeviceAccessor,
                       }

def createAccessor(baseAddress, *args):
    url_parts = compat_urlsplit(baseAddress, allow_fragments = False)

    assert url_parts.scheme in SUPPORTED_ACCESSORS.keys()
    return SUPPORTED_ACCESSORS[url_parts.scheme](baseAddress, *args)
