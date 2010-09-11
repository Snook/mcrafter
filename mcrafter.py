#!/usr/bin/python
#
# mcrafter.py - Manages Minecraft servers in screen, SMP or Classic
# Usage: ./mcrafter.py {start|stop|restart|backup|update|screen|help}
#
# Ryan Snook
# https://github.com/snook
#

import os, sys, re, time, shutil, tarfile
from subprocess import Popen, PIPE

os.chdir(os.path.dirname(sys.argv[0]))

def server_binary():
    if os.path.isfile("minecraft-server.jar"):
        return "minecraft-server.jar"
    elif os.path.isfile("craftbukkit-0.0.1-SNAPSHOT.jar"):
        return "craftbukkit-0.0.1-SNAPSHOT.jar"
    elif os.path.isfile("minecraft_server.jar"):
        return "minecraft_server.jar"

def server_classic():
    if os.path.isfile("minecraft-server.jar"):
        return True
    elif os.path.isfile("minecraft_server.jar"):
        return False

def server_popen(arg):
    return Popen(arg, shell=True, stdout=PIPE, stderr=PIPE, close_fds=True, universal_newlines=True)

def server_screencheck(arg):
    CWD = os.path.basename(os.getcwd())

    screenname = "mc_%s" % CWD
    screen = 0

    p = server_popen("screen -ls")
    stdout, stderr = p.communicate()
    if not stdout and p.returncode > 1:
        # either problem with screen or it is not installed
        screen = 0
    for line in stdout.split('\n'):
        line = line.strip()
        try:
            x, y, z = [ line.index(c) for c in '.()' ]
            if not (x < y < z):
                continue

            pid = line[:x].strip()
            name = line[x+1:y].strip()
            state = line[y+1:z].strip()

            if pid < 1:
                screen = 0
                break
            if arg == pid + "." + screenname:
                screen = 1
                break

        except (ValueError), e:
            continue

    if screen == 1:
        return 1
    else:
        return 0

def server_screenname():
    CWD = os.path.basename(os.getcwd())

    screenname = "mc_%s" % CWD

    #sessions = []
    p = server_popen("screen -ls")
    stdout, stderr = p.communicate()
    if not stdout and p.returncode > 1:
        # either problem with screen or it is not installed
        return screenname
    for line in stdout.split('\n'):
        line = line.strip()
        try:
            x, y, z = [ line.index(c) for c in '.()' ]
            if not (x < y < z):
                continue

            pid = line[:x].strip()
            name = line[x+1:y].strip()
            state = line[y+1:z].strip()

            if name == screenname:
                screenname = pid + "." + screenname
                break

            #sessions.append((pid, name, state))

        except (ValueError), e:
            continue
    return screenname

def server_start():
    if not server_screencheck(server_screenname()):
        if server_classic():
            server = server_popen("screen -dmLS " + server_screenname() + " java -cp minecraft-server.jar com.mojang.minecraft.server.MinecraftServer" )
        else:
            server = server_popen("screen -dmLS " + server_screenname() + " java -Xmx1024M -Xms1024M -jar " + server_binary() + " nogui" )
        print "Server started in screen %s" % server_screenname()
    else:
        print "Server already started in screen %s, can not start again" % server_screenname()

def server_stop():
    if server_classic():
        server_popen("screen -S %s -X stuff \"quit\n\"" % server_screenname() )
        try:
            os.unlink("players.txt")
        except os.error:
            pass
    else:
        server_popen("screen -S %s -X stuff \"stop\n\"" % server_screenname() )
    print "Server stopped"

def server_screen():
    server_popen("screen -raAd %s" % server_screenname() )

def server_restart():
    print "Server restarting"
    server_stop()
    print "Server starting in 5 seconds..."
    time.sleep(5)
    server_start()

def server_backup():
    print "Backup processing..."
    if not os.path.exists("backups_mcrafter"):
        os.mkdir("backups_mcrafter")
    if server_classic():
        backupname = "server_level-%s.tar.gz" % int(time.time())
        if not os.path.exists(backupname):
            tar = tarfile.open(backupname, "w:gz")
            tar.add("server_level.dat")
            tar.close()
    else:
        file = open("server.properties")
        for line in file:
            tokens = line.split("=")
            if tokens[0] == "level-name":
                level = tokens[1].strip("\n")
        backupname = level + "-%s.tar.gz" % int(time.time())
        if not os.path.exists(backupname):
            server_popen("screen -S %s -X stuff \"save-all\n\"" % server_screenname() )
            server_popen("screen -S %s -X stuff \"save-off\n\"" % server_screenname() )
            tar = tarfile.open(backupname, "w:gz")
            tar.add(level)
            tar.close()
            server_popen("screen -S %s -X stuff \"save-on\n\"" % server_screenname() )
    shutil.move(backupname, "backups_mcrafter/")
    print "Backup " + backupname + " complete"

def server_update():
    if server_classic():
        file = server_popen("wget -N http://www.minecraft.net/minecraft-server.zip 2>&1")
    else:
        file = server_popen("wget -N https://s3.amazonaws.com/MinecraftDownload/launcher/minecraft_server.jar 2>&1")
    if re.search("sizes do not match", file.stdout.read()):
        if server_classic():
            import zipfile
            zipfile.ZipFile("minecraft-server.zip").extractall()
            try:
                os.unlink("start server.bat")
            except os.error:
                pass
        print "Server updated"
        server_restart()
    else:
        print "Server updates not found"

def main(arg):
    if arg == "start":
        server_start()
        sys.exit()
    elif arg == "stop":
        server_stop()
        sys.exit()
    elif arg == "restart":
        server_restart()
        sys.exit()
    elif arg == "update":
        server_update()
        sys.exit()
    elif arg == "screen":
        server_screen()
        sys.exit()
    elif arg == "backup":
        server_backup()
        sys.exit()
    else:
        print """Usage: ./mcrafter.py {start|stop|restart|backup|update|screen|help}
    Ctrl-A, D to exit screen"""

if __name__ == '__main__':
    main(' '.join(sys.argv[1:]))