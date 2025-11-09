#ifndef COMMON_H
#define COMMON_H

#define SOCKET_PATH	"/tmp/usage-bar.sock"
#define WINDOW_WIDTH	192
#define WINDOW_HEIGHT	108
#define MAX_SCREENS	16
#define SMALL_WINDOW_SIZE	20

/* NotificationState enum values */
#define STATE_UNKNOWN		-1
#define STATE_BREAK_OVER	0
#define STATE_BREAK		1
#define STATE_TYPING		2
#define STATE_OVERSPEED		3
#define STATE_BREAK_DUE		4

/* Color definitions from colors.md */
#define COLOR_UNKNOWN		0x000000  /* black - initial state */
#define COLOR_BREAK_OVER	0x007051  /* green */
#define COLOR_BREAK		    0x142f8c  /* blue */
#define COLOR_TYPING		0x8C4914  /* orange */
#define COLOR_OVERSPEED		0xB70000  /* red */
#define COLOR_BREAK_DUE		0xFF6D00  /* orange for break_due */

#endif /* COMMON_H */
