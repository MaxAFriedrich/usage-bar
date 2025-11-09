#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/extensions/Xinerama.h>

#define SOCKET_PATH	"/tmp/usage-bar.sock"
#define WINDOW_WIDTH	192
#define WINDOW_HEIGHT	108
#define MAX_SCREENS	16
#define SMALL_WINDOW_SIZE	20

/* NotificationState enum values */
#define STATE_BREAK_OVER	0
#define STATE_BREAK		1
#define STATE_TYPING		2
#define STATE_OVERSPEED		3
#define STATE_BREAK_DUE		4

/* Color definitions from colors.md */
#define COLOR_BREAK_OVER	0x007051  /* green */
#define COLOR_BREAK		0x142f8c  /* blue */
#define COLOR_TYPING		0x8C4914  /* orange */
#define COLOR_OVERSPEED		0xB70000  /* red */
#define COLOR_BREAK_DUE		0xFF6D00  /* orange for break_due */

struct screen_window {
	Window window;
	GC gc;
	int x;
	int y;
	int width;
	int height;
};

struct window_state {
	Display *display;
	struct screen_window screens[MAX_SCREENS];
	int num_screens;
	int is_visible;
	int current_state;
};

static void init_x11(struct window_state *ws)
{
	int screen, num_screens, i;
	XineramaScreenInfo *screens;
	XSetWindowAttributes attrs;

	ws->display = XOpenDisplay(NULL);
	if (!ws->display) {
		fprintf(stderr, "Cannot open X display\n");
		exit(1);
	}

	screen = DefaultScreen(ws->display);
	screens = XineramaQueryScreens(ws->display, &num_screens);

	if (screens && num_screens > 0) {
		ws->num_screens = (num_screens > MAX_SCREENS) ?
				  MAX_SCREENS : num_screens;

		for (i = 0; i < ws->num_screens; i++) {
			ws->screens[i].width = screens[i].width;
			ws->screens[i].height = screens[i].height;
			ws->screens[i].x = screens[i].x_org;
			ws->screens[i].y = screens[i].y_org;

			ws->screens[i].window = XCreateSimpleWindow(
				ws->display,
				RootWindow(ws->display, screen),
				ws->screens[i].x, ws->screens[i].y,
				WINDOW_WIDTH, WINDOW_HEIGHT,
				0,
				BlackPixel(ws->display, screen),
				WhitePixel(ws->display, screen)
			);

			attrs.override_redirect = True;
			XChangeWindowAttributes(ws->display,
						ws->screens[i].window,
						CWOverrideRedirect, &attrs);

			ws->screens[i].gc = XCreateGC(ws->display,
						      ws->screens[i].window,
						      0, NULL);
		}

		XFree(screens);
	} else {
		ws->num_screens = 1;
		ws->screens[0].width = DisplayWidth(ws->display, screen);
		ws->screens[0].height = DisplayHeight(ws->display, screen);
		ws->screens[0].x = 0;
		ws->screens[0].y = 0;

		ws->screens[0].window = XCreateSimpleWindow(
			ws->display,
			RootWindow(ws->display, screen),
			ws->screens[0].x, ws->screens[0].y,
			WINDOW_WIDTH, WINDOW_HEIGHT,
			0,
			BlackPixel(ws->display, screen),
			WhitePixel(ws->display, screen)
		);

		attrs.override_redirect = True;
		XChangeWindowAttributes(ws->display, ws->screens[0].window,
					CWOverrideRedirect, &attrs);

		ws->screens[0].gc = XCreateGC(ws->display,
					      ws->screens[0].window, 0, NULL);
	}

	ws->is_visible = 0;
	ws->current_state = -1;
}

static void show_overspeed_window(struct window_state *ws)
{
	const char *text = "OVERSPEED";
	XFontStruct *font;
	int text_width, text_x, text_y;
	int i, center_x, center_y;

	if (ws->is_visible && ws->current_state == STATE_OVERSPEED)
		return;

	for (i = 0; i < ws->num_screens; i++) {
		center_x = ws->screens[i].x + (ws->screens[i].width - WINDOW_WIDTH) / 2;
		center_y = ws->screens[i].y + (ws->screens[i].height - WINDOW_HEIGHT) / 2;

		XMoveWindow(ws->display, ws->screens[i].window, center_x, center_y);
		XResizeWindow(ws->display, ws->screens[i].window, WINDOW_WIDTH, WINDOW_HEIGHT);
		XMapRaised(ws->display, ws->screens[i].window);

		XSetForeground(ws->display, ws->screens[i].gc, COLOR_OVERSPEED);
		XFillRectangle(ws->display, ws->screens[i].window,
			       ws->screens[i].gc, 0, 0,
			       WINDOW_WIDTH, WINDOW_HEIGHT);

		XSetForeground(ws->display, ws->screens[i].gc, 0x7C7C7C);

		font = XLoadQueryFont(ws->display,
				      "-*-helvetica-bold-r-*-*-32-*-*-*-*-*-*-*");
		if (!font)
			font = XLoadQueryFont(ws->display, "fixed");

		if (font)
			XSetFont(ws->display, ws->screens[i].gc, font->fid);

		text_width = XTextWidth(font, text, strlen(text));
		text_x = (WINDOW_WIDTH - text_width) / 2;
		text_y = WINDOW_HEIGHT / 2 + 16;

		XDrawString(ws->display, ws->screens[i].window,
			    ws->screens[i].gc, text_x, text_y,
			    text, strlen(text));

		if (font)
			XFreeFont(ws->display, font);
	}

	XFlush(ws->display);
	ws->is_visible = 1;
	ws->current_state = STATE_OVERSPEED;
}

static void hide_overspeed_window(struct window_state *ws)
{
	int i;

	if (!ws->is_visible)
		return;

	for (i = 0; i < ws->num_screens; i++)
		XUnmapWindow(ws->display, ws->screens[i].window);

	XFlush(ws->display);
	ws->is_visible = 0;
}

static void show_break_due_window(struct window_state *ws)
{
	const char *text = "BREAK";
	XFontStruct *font;
	int text_width, text_x, text_y;
	int i, center_x, center_y;

	if (ws->is_visible && ws->current_state == STATE_BREAK_DUE)
		return;

	for (i = 0; i < ws->num_screens; i++) {
		center_x = ws->screens[i].x + (ws->screens[i].width - WINDOW_WIDTH) / 2;
		center_y = ws->screens[i].y + (ws->screens[i].height - WINDOW_HEIGHT) / 2;

		XMoveWindow(ws->display, ws->screens[i].window, center_x, center_y);
		XResizeWindow(ws->display, ws->screens[i].window, WINDOW_WIDTH, WINDOW_HEIGHT);
		XMapRaised(ws->display, ws->screens[i].window);

		XSetForeground(ws->display, ws->screens[i].gc, COLOR_BREAK_DUE);
		XFillRectangle(ws->display, ws->screens[i].window,
			       ws->screens[i].gc, 0, 0,
			       WINDOW_WIDTH, WINDOW_HEIGHT);

		XSetForeground(ws->display, ws->screens[i].gc, 0x7C7C7C);

		font = XLoadQueryFont(ws->display,
				      "-*-helvetica-bold-r-*-*-32-*-*-*-*-*-*-*");
		if (!font)
			font = XLoadQueryFont(ws->display, "fixed");

		if (font)
			XSetFont(ws->display, ws->screens[i].gc, font->fid);

		text_width = XTextWidth(font, text, strlen(text));
		text_x = (WINDOW_WIDTH - text_width) / 2;
		text_y = WINDOW_HEIGHT / 2 + 16;

		XDrawString(ws->display, ws->screens[i].window,
			    ws->screens[i].gc, text_x, text_y,
			    text, strlen(text));

		if (font)
			XFreeFont(ws->display, font);
	}

	XFlush(ws->display);
	ws->is_visible = 1;
	ws->current_state = STATE_BREAK_DUE;
}

static void show_small_indicator(struct window_state *ws, int state)
{
	int i;
	unsigned long color;

	switch (state) {
	case STATE_BREAK_OVER:
		color = COLOR_BREAK_OVER;
		break;
	case STATE_BREAK:
		color = COLOR_BREAK;
		break;
	case STATE_TYPING:
		color = COLOR_TYPING;
		break;
	default:
		return;
	}

	if (ws->is_visible && ws->current_state == state)
		return;

	for (i = 0; i < ws->num_screens; i++) {
		XMoveWindow(ws->display, ws->screens[i].window, 
			    ws->screens[i].x, ws->screens[i].y);
		XResizeWindow(ws->display, ws->screens[i].window, 
			      SMALL_WINDOW_SIZE, SMALL_WINDOW_SIZE);
		XMapRaised(ws->display, ws->screens[i].window);

		XSetForeground(ws->display, ws->screens[i].gc, color);
		XFillRectangle(ws->display, ws->screens[i].window,
			       ws->screens[i].gc, 0, 0,
			       SMALL_WINDOW_SIZE, SMALL_WINDOW_SIZE);
	}

	XFlush(ws->display);
	ws->is_visible = 1;
	ws->current_state = state;
}

static void hide_all_windows(struct window_state *ws)
{
	hide_overspeed_window(ws);
	ws->current_state = -1;
}

static void cleanup_x11(struct window_state *ws)
{
	int i;

	for (i = 0; i < ws->num_screens; i++) {
		if (ws->screens[i].gc)
			XFreeGC(ws->display, ws->screens[i].gc);
		if (ws->screens[i].window)
			XDestroyWindow(ws->display, ws->screens[i].window);
	}
	if (ws->display)
		XCloseDisplay(ws->display);
}

static int connect_to_socket(void)
{
	struct sockaddr_un addr;
	int sock;

	sock = socket(AF_UNIX, SOCK_STREAM, 0);
	if (sock == -1) {
		perror("socket");
		return -1;
	}

	memset(&addr, 0, sizeof(addr));
	addr.sun_family = AF_UNIX;
	strncpy(addr.sun_path, SOCKET_PATH, sizeof(addr.sun_path) - 1);

	if (connect(sock, (struct sockaddr *)&addr, sizeof(addr)) == -1) {
		perror("connect");
		close(sock);
		return -1;
	}

	return sock;
}

int main(void)
{
	struct window_state ws = {0};
	char buffer[256];
	ssize_t n;
	int sock, state;

	init_x11(&ws);

	printf("Connecting to socket at %s\n", SOCKET_PATH);

	while (1) {
		sock = connect_to_socket();
		if (sock == -1) {
			fprintf(stderr,
				"Failed to connect to socket, retrying in 5 seconds...\n");
			sleep(5);
			continue;
		}

		printf("Connected to socket\n");

		while ((n = read(sock, buffer, sizeof(buffer) - 1)) > 0) {
			buffer[n] = '\0';
			state = atoi(buffer);

			printf("Received state: %d\n", state);

			switch (state) {
			case STATE_OVERSPEED:
				printf("OVERSPEED detected!\n");
				show_overspeed_window(&ws);
				break;
			case STATE_BREAK_DUE:
				printf("BREAK DUE!\n");
				show_break_due_window(&ws);
				break;
			case STATE_BREAK_OVER:
			case STATE_BREAK:
			case STATE_TYPING:
				show_small_indicator(&ws, state);
				break;
			default:
				hide_all_windows(&ws);
				break;
			}
		}

		close(sock);
		printf("Disconnected from socket, reconnecting...\n");
		sleep(1);
	}

	cleanup_x11(&ws);
	return 0;
}
