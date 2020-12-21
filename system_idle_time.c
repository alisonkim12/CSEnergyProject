/* To compile:
 *   gcc -g -Wall -o system_idle_time system_idle_time.c -lXss -lX11
 */


/* KCW: this seems to require permission via xauth.
 * If you run:  ps aux | grep X
 * You'll see Xorg processes running with "-auth /var/.../:N.Xauth" arguments.
 * Those tell you where the auth files are.  If you add those files with
 * 'xauth', any user can call XOpenDisplay().
 *
 * See:
 * http://blog.fox.geek.nz/2012/10/granting-root-access-to-all-xorg-x11.html
 */

#include <dirent.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <time.h>
#include <unistd.h>

#include <X11/extensions/scrnsaver.h>
#include <X11/Xlib.h>

int main(void) {
    /* The min and max idle times we've seen across all displays. */
    unsigned long min = 0;
    unsigned long max = 0;

    /* Flag to indicate whether it's the first display we've encountered. */
    int first = 1;

    /* Open the directory that contains information about X11 displays. */
    DIR* d = opendir("/tmp/.X11-unix");

    if (d != NULL) {
        struct dirent *dr;

        while ((dr = readdir(d)) != NULL) {
            char display_name[64] = ":";
            char xauth_path[256];

            if (dr->d_name[0] != 'X')
                continue;

            /* Build the display number. */
            strncat(display_name, dr->d_name + 1, 62);

            /* Embed the display number into the system path where xauth files
             * live.  Currently /var/lib/mdm/. */
            snprintf(xauth_path, 256, "/var/lib/mdm/%s.Xauth", display_name);

            if (setenv("XAUTHORITY", xauth_path, 1)) {
                printf("Failed to set XAUTHORITY for display %s\n", display_name);
                continue;
            }

            /* Attempt to open the display. */
            Display *disp = XOpenDisplay(display_name);
            if (disp != NULL) {
                /* Query idle time. */
                XScreenSaverInfo *info = XScreenSaverAllocInfo();
                XScreenSaverQueryInfo(disp, DefaultRootWindow(disp), info);

                if (first) {
                    min = info->idle;
                    max = info->idle;
                    first = 0;
                }

                if (info->idle < min) {
                    min = info->idle;
                }

                if (info->idle > max) {
                    max = info->idle;
                }

                XFree(info);
                XCloseDisplay(disp);
            } else {
                fprintf(stderr, "Failed to open display: %s\n", display_name);
            }
        }
        closedir(d);
    }

    /* Check ssh connections. */
    if (chdir("/dev/pts")) {
        d = NULL;
    } else {
        d = opendir("/dev/pts");
    }

    if (d != NULL) {
        struct dirent *dr;

        while ((dr = readdir(d))) {
            struct stat sbuf;
            unsigned long idle_time;

            if (dr->d_name[0] == '.') {
                continue;
            }

            if (stat(dr->d_name, &sbuf)) {
                continue;
            }

            idle_time = (time(NULL) - sbuf.st_atime) * 1000;

            if (first) {
                min = idle_time;
                max = idle_time;
                first = 0;
            }

            if (idle_time < min) {
                min = idle_time;
            }

        }

        closedir(d);
    }

    if (first) {
        /* We never found any idle time data -- nobody logged in? */
        printf("-1 -1\n");
    } else {
        /* Print the min/max idle time data we found. */
        printf("%lu %lu\n", min, max);
    }

    return 0;
}
