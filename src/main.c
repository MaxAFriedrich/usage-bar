#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include "common.h"
#include "window.h"
#include "socket.h"

int main(void)
{
	struct window_state ws = {0};
	char buffer[256];
	ssize_t n;
	int sock, state;

	init_x11(&ws);

	/* Show black indicator on startup until we receive first state */
	show_small_indicator(&ws, STATE_UNKNOWN);

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
