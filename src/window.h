#ifndef WINDOW_H
#define WINDOW_H

#include <X11/Xlib.h>
#include "common.h"

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

void init_x11(struct window_state *ws);
void cleanup_x11(struct window_state *ws);
void show_overspeed_window(struct window_state *ws);
void show_break_due_window(struct window_state *ws);
void show_small_indicator(struct window_state *ws, int state);
void hide_all_windows(struct window_state *ws);

#endif /* WINDOW_H */
