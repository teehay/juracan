# juracan
usage: juracan_1.5.py [-h] [-s dbpath tablename]
                      [-m host dbname tblname user password] [-c] [-r]
                      [-e [path]] [-b [path]] [-d [initial]] [-q]
                      [keyword]

Gets ASN and ISP addresses related to the target keyword from the Hurricane
Electric Internet Services website. Please do not abuse this service!

!!! Currently not functional because of changes in the HTML of the target database results, easily fixed by changing all references to the old structure. !!!

positional arguments:
  keyword               target keyword

optional arguments:
  -h, --help >           show this help message and exit
  -s dbpath tablename, --sqlite dbpath tablename >
                        store results in a SQLite database; creates a new
                        database and table if they don't already exist
  -m host dbname tblname user password, --mysql host dbname tblname user password >
                        store results in a MySQL database; creates a new
                        database and table if they don't exist
  -c, --csv >            output table data as a CSV list
  -r, --result >         output the result column data only; if --csv is on,
                        result column data is output as a CSV list
  -e [path], --exec [path] >
                        specify the location path to the driver executable
                        that will be used; checks system path by default
  -b [path], --binary [path] >
                        specify the location path to the browser binary that
                        will be used; checks common locations by default
  -d [initial], --driver [initial] >
                        specify the browser driver that will be used in the
                        search; options: c[hrome], g[ecko]; default: g
  -q, --quiet >          run script with no screen output
