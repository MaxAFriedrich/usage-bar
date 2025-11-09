#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/extensions/Xinerama.h>
#include "window.h"
#include "common.h"

void init_x11(struct window_state *ws)
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

void cleanup_x11(struct window_state *ws)
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

static void show_large_window(struct window_state *ws, const char *text,
			      unsigned long bg_color, int state)
{
	XFontStruct *font;
	int text_width, text_x, text_y;
	int i, center_x, center_y;

	if (ws->is_visible && ws->current_state == state)
		return;

	for (i = 0; i < ws->num_screens; i++) {
		center_x = ws->screens[i].x + (ws->screens[i].width - WINDOW_WIDTH) / 2;
		center_y = ws->screens[i].y + (ws->screens[i].height - WINDOW_HEIGHT) / 2;

		XMoveWindow(ws->display, ws->screens[i].window, center_x, center_y);
		XResizeWindow(ws->display, ws->screens[i].window, WINDOW_WIDTH, WINDOW_HEIGHT);
		XMapRaised(ws->display, ws->screens[i].window);

		XSetForeground(ws->display, ws->screens[i].gc, bg_color);
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
	ws->current_state = state;
}

void show_overspeed_window(struct window_state *ws)
{
	show_large_window(ws, "OVERSPEED", COLOR_OVERSPEED, STATE_OVERSPEED);
}

void show_break_due_window(struct window_state *ws)
{
	show_large_window(ws, "BREAK", COLOR_BREAK_DUE, STATE_BREAK_DUE);
}

void show_small_indicator(struct window_state *ws, int state)
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

void hide_all_windows(struct window_state *ws)
{
	int i;

	if (!ws->is_visible)
		return;

	for (i = 0; i < ws->num_screens; i++)
		XUnmapWindow(ws->display, ws->screens[i].window);

	XFlush(ws->display);
	ws->is_visible = 0;
	ws->current_state = -1;
}
