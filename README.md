# extractAttachment
this python cli script allows to extract defined attachments from mail files.  
It uses python email class to parse a file for attachments. Only default python libs, that should be shipped in every python installation, are used.

Currently it expects the given filename to start with a digit like dovecot server does name the mail files.  
If you need the script to read ANY file in given dir, then apply no_filename_filter.patch

## Usage
```
extract.py -s|--source <str source> -o|--out <str output> -h|--hash <str digest> -t|--type <str type>
-s|--source	defines the directory/file to read
		defaults to cwd
-o|--out	defines the directory to write extracted file to
		defaults to output on STDOUT
-h|--hash	if set defines the digest to use to hash extracted file content
		defaults to sha1
		supported digests:
			md5
			sha1
			sha224
			sha256
			sha384
			sha512
-t|--type	string of mime types to extract
		default to 'application/octet-stream'
		provide a plain string or a python regex string
			application/octect-stream
			application/.*$
			.*/pdf$
			(application|text|image|video)/.*$
```
