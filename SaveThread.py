
import paramiko
import os
from tifffile import imsave

def file_save_process(queue,stop_token, metadata_dictionary,ssh_opts):

    while True:
        token = queue.get()
        if token == stop_token:
            return
        else:
            (slice_index,frame_index, z_index, prot_name, path, data, ch, x, y, z,triggerflag) = token
            tif_filepath = os.path.join(path, prot_name + "_S%04d_F%04d_Z%02d.tif" % (slice_index, frame_index, z_index))
            metadata_filepath = os.path.join(path, prot_name + "_S%04d_F%04d_Z%02d_metadata.txt"%(slice_index, frame_index, z_index))
            imsave(tif_filepath,data)
            write_slice_metadata(metadata_filepath, ch, x, y, z, slice_index, triggerflag, metadata_dictionary,ssh_opts)


def write_slice_metadata(filename, ch, xpos, ypos, zpos, slice_index,triggerflag, meta_dict,ssh_opts):
    channelname    = meta_dict['channelname'][ch]
    (height,width) = meta_dict['(height,width)']
    ScaleFactorX   = meta_dict['ScaleFactorX']
    ScaleFactorY   = meta_dict['ScaleFactorY']
    exp_time       = meta_dict['exp_time'][ch]

    f = open(filename, 'w')
    f.write("Channel\tWidth\tHeight\tMosaicX\tMosaicY\tScaleX\tScaleY\tExposureTime\n")
    f.write("%s\t%d\t%d\t%d\t%d\t%f\t%f\t%f\n" % \
    (channelname, width, height, 1, 1, ScaleFactorX, ScaleFactorY, exp_time))
    f.write("XPositions\tYPositions\tFocusPositions\n")
    f.write("%s\t%s\t%s\n" %(xpos, ypos, zpos))
    if triggerflag == True:


        if ssh_opts['do_ssh_trigger']:
            fname =ssh_opts['cron_dir']
            sessiondir, frametitle = os.path.split(filename)
            sessiondir, chname = os.path.split(sessiondir)
            print "Session Directory", sessiondir
            sessiondir = '/'.join(sessiondir.split('\\'))
            junk, sessiondir = sessiondir.split(':')
            print 'mount point is', ssh_opts['mount_point']
            #sessiondir = os.path.join(ssh_opts['mount_point'], sessiondir)
            sessiondir = ssh_opts['mount_point']+'/'+sessiondir
            print sessiondir
            meta_experiment_name = ssh_opts['meta_experiment_name']
            outputstring = "%s,%s,%s"%(sessiondir,slice_index,meta_experiment_name)

            #linux command to dump outputstring to filename
            cmd = "echo %s > %s"%(outputstring,fname)

            #run the command via ssh to machine ibs-sharmi-ux1
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                ssh.connect(ssh_opts['host'], username=ssh_opts['username'], password=ssh_opts['password'], timeout = ssh_opts['timeout'])
                ssh.exec_command(cmd)
            except paramiko.ssh_exception.SSHException:
                print "failed to trigger SSH to %s@%s"%(ssh_opts['host'],ssh_opts['username'])

