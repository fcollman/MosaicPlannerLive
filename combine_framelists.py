import os

date = "2013-03-20"
ribbon = "Ex2-R18"
session = "session6"
root = os.path.normpath("C:\%s" % os.path.join("Axiovision Images", "%s_%s_%s" % (date, ribbon, session)))
print root
#root.rstrip("\")

cols = ['C1', 'C2']
nframes = 3
flist_names = []
flist_paths = []
flists = []
for col in cols:
    #flist_name_tmp = "%s_%s_%s_%sL4_posList-frames1x3.csv" %(date, ribbon, session, col)
    flist_name_tmp = "%s_%s_%s_%sL4-posList_frames-rot-1x3.csv" % (date, ribbon, session, col)
    flist_names.append(flist_name_tmp)
    flist_path_tmp = os.path.join(root, flist_name_tmp)
    print flist_path_tmp
    flist_paths.append(flist_path_tmp)

for path in flist_paths:
    with open(path, 'r') as f:
        print "opened %s" % path
        flists.append(f.readlines())
    assert f.closed is True
    

newpath = os.path.join(root, "%s_%s_%s_combined-posList_frames-rot-1x3.csv" % (date, ribbon, session))


with open(newpath, 'w') as f:
    print "newpath: %s" % newpath
    # write header lines from first input file
    for line in range(7):
        f.write(flists[0][line])
    # interleave lines from input files into output file
    assert (len(flists[0])-7) % nframes == 0
    # for each section
    for secnum in range((len(flists[0])-7)/nframes):
        print "secnum %d" % secnum
        # for each column in the section
        for colnum in range(len(cols)):
            print "colnum %d" % colnum
            # for each frame in the column
            for fnum in range(nframes):
                print "fnum %d" % fnum
                line = 7+(secnum*nframes)+fnum
                print "line %d" % line
                f.write('"%s_%s' % (cols[colnum], flists[colnum][line][1::]))
                print '"%s_%s' % (cols[colnum], flists[colnum][line][1::])
assert f.closed is True
print "saved to %s" %newpath