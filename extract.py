import email
import getopt
import hashlib
import os
import os.path
import random
import re
import string
import sys
from errno import EACCES, EPERM, ENOENT
from os import walk


def main(argv):
    """parses cli arguments

    :param argv: cli arguments
    :param outdir: directory to save extracted attachments default to None aka print on STDOUT
    :param sourcedir: directory/filepath to read content of file from default to ./
    :param hash: digest to use for attachment hashing default to None
    :param type: mime content type header to search for default to application/octet-stream
    :return: void
    :raises: IOError: if sourcedir is not existing directory or file
    :except: IOError: catches EPERM, EACCES and ENOENT thrown in subactions
    """
    # set some sane defaults
    outdir = None
    sourcedir = './'
    hash = None
    type = 'application/octet-stream$'
    # read arguments from cli
    try:
        opts, args = getopt.getopt(argv, "h:s:o:t:", ["hash", "source", "out", "type"])
    # show help if parsing cli arguments fails
    except getopt.GetoptError:
        print 'extract.py -s|--source <str source> -o|--out <str output> -h|--hash <str digest> -t|--type <str type>'
        print "-s|--source\tdefines the directory/file to read\r\n\t\tdefaults to cwd"
        print "-o|--out\tdefines the directory to write extracted file to\r\n\t\tdefaults to output on STDOUT"
        print "-h|--hash\tif set defines the digest to use to hash extracted file content\r\n\t\tdefaults to sha1\r\n\t\tsupported digests:\r\n\t\t\tmd5\r\n\t\t\tsha1\r\n\t\t\tsha224\r\n\t\t\tsha256\r\n\t\t\tsha384\r\n\t\t\tsha512"
        print "-t|--type\tstring of mime types to extract\r\n\t\tdefault to 'application/octet-stream'\r\n\t\tprovide a plain string or a python regex string\r\n\t\t\tapplication/octect-stream\r\n\t\t\tapplication/.*$\r\n\t\t\t.*/pdf$\r\n\t\t\t(application|text|image|video)/.*$"
        sys.exit(2)
    # add cli arguments to variables
    for opt, arg in opts:
        if opt in ('-s', '--source'):
            sourcedir = arg
        elif opt in ('-o', '--out'):
            outdir = arg
        elif opt in ('-h', '--hash'):
            allowed = ['md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512']
            if arg in allowed:
                hash = arg
            else:
                print 'unknown digest type ' + arg
                print 'supported digests ' + " ".join(allowed)
                sys.exit(1)
        elif opt in ('-t', '--type'):
            type = arg
    # directory provided as sourcedir, read all files from it
    if os.path.isdir(sourcedir):
        # loop over list of files in given directory
        for file in readFileNames(sourcedir=sourcedir):
            # extract attachment(s) from file
            try:
                extractAttachment(file=file, outdir=outdir, sourcedir=sourcedir, digest=hash, type=type)
            except IOError as e:
                if e.errno == EPERM or e.errno == EACCES:
                    print('not allowed to access ' + sourcedir + '/' + file + ' check permissions!')
                elif e.errno == ENOENT:
                    print('could not find ' + sourcedir)
    # file provided as sourcedir, just read the file nothing else
    elif os.path.isfile(sourcedir):
        sourcedir, file = os.path.split(sourcedir)
        try:
            extractAttachment(file=file, outdir=outdir, sourcedir=sourcedir, digest=hash, type=type)
        except IOError as e:
            if e.errno == EPERM or e.errno == EACCES:
                print('not allowed to access ' + sourcedir + '/' + file + ' check permissions!')
            elif e.errno == ENOENT:
                print('could not find ' + sourcedir)
    else:
        raise IOError('could not find ' + sourcedir)


def readFileNames(sourcedir='./'):
    """read files from given directory

    :param sourcedir: directory/file to read
    :return: list: list of filenames
    :raises: IOError: missing X and/or R permission on sourcedir
    """
    if not os.access(sourcedir, os.R_OK | os.X_OK): raise IOError(
        'not allowed to access ' + sourcedir + ' check permissions!')
    f = []
    # filter for filenames starting with numbers
    # ex dovecot message files
    r = re.compile("^[0-9]+.*$")
    for (dirpath, dirnames, filenames) in walk(sourcedir):
        f.extend(filter(r.match, filenames))
        # f.extend(filenames)
    return f


def extractAttachment(file=None, outdir=None, sourcedir=None, digest=None, type='application/octet-stream$'):
    """reads content from file and extracts matching attachments

    :param file: filename to read content from
    :param outdir: directory to save extracted attachments
    :param sourcedir: directory to read content of file from
    :param digest: digest to use for attachment hashing
    :param type: mime content type header to search for
    :except: OSError: catches EPERM, EACCES and ENOENT
    :raises: IOError: if dir/file does not exist or missing permissions
    :return: void
    """
    r = re.compile("^" + type)
    # generate a hash of filename of the message
    # avoids necessary escapes when using a filename to write content to
    hash = hashlib.sha256(file).hexdigest()
    try:
        with open(sourcedir + '/' + file) as fl:
            msg = email.message_from_file(fl)
    except OSError as e:
        if e.errno == EPERM or e.errno == EACCES:
            raise IOError('not allowed to access ' + sourcedir + '/' + file + ' check permissions!')
        elif e.errno == ENOENT:
            raise IOError('could not find ' + sourcedir)
    for part in msg.walk():
        if r.match(part.get_content_type()):
            if digest is None:
                if outdir is not None:
                    try:
                        filename = "".join(os.path.splitext(part.get_filename()))
                    except Exception as e:
                        filename = ''.join(
                            random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(12))
                    with open(outdir + '/' + hash + '_' + "".join(os.path.splitext(filename)), 'w') as fl:
                        fl.write(part.get_payload(decode=True).replace('\r', "\r\n"))
                else:
                    print part.get_payload(decode=True).replace('\r', "\r\n")
            else:
                # do not change any bit of the source for hashing --> decode=False
                # and no eol replacements
                if digest == 'sha256':
                    print hashlib.sha256(part.get_payload(decode=False)).hexdigest()
                elif digest == 'sha512':
                    print hashlib.sha512(part.get_payload(decode=False)).hexdigest()
                elif digest == 'md5':
                    print hashlib.md5(part.get_payload(decode=False)).hexdigest()
                elif digest == 'sha1':
                    print hashlib.sha1(part.get_payload(decode=False)).hexdigest()
                elif digest == 'sha224':
                    print hashlib.sha224(part.get_payload(decode=False)).hexdigest()
                elif digest == 'sha384':
                    print hashlib.sha384(part.get_payload(decode=False)).hexdigest()
                else:
                    print hashlib.sha1(part.get_payload(decode=False)).hexdigest()


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except IOError as e:
        print e
