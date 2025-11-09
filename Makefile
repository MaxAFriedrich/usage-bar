CC = gcc
CFLAGS = -Wall -Wextra -O2 -Isrc
LIBS = -lX11 -lXinerama

TARGET = overspeed_monitor
SRCDIR = src
OBJS = $(SRCDIR)/main.o $(SRCDIR)/window.o $(SRCDIR)/socket.o

PREFIX ?= /usr/local
BINDIR = $(PREFIX)/bin
SYSTEMD_USER_DIR = $(HOME)/.config/systemd/user

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $(TARGET) $(OBJS) $(LIBS)

$(SRCDIR)/%.o: $(SRCDIR)/%.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(TARGET) $(SRCDIR)/*.o

install: all
	install -d $(BINDIR)
	install -m 755 $(TARGET) $(BINDIR)/
	install -m 755 input_monitor.py $(BINDIR)/usage-bar-monitor
	install -d $(SYSTEMD_USER_DIR)
	sed 's|@BINDIR@|$(BINDIR)|g' systemd/usage-bar-monitor.service > $(SYSTEMD_USER_DIR)/usage-bar-monitor.service
	sed 's|@BINDIR@|$(BINDIR)|g' systemd/usage-bar-gui.service > $(SYSTEMD_USER_DIR)/usage-bar-gui.service
	systemctl --user daemon-reload
	@echo "Services installed. Enable and start with:"
	@echo "  systemctl --user enable --now usage-bar-monitor.service"
	@echo "  systemctl --user enable --now usage-bar-gui.service"

uninstall:
	systemctl --user stop usage-bar-monitor.service usage-bar-gui.service 2>/dev/null || true
	systemctl --user disable usage-bar-monitor.service usage-bar-gui.service 2>/dev/null || true
	rm -f $(SYSTEMD_USER_DIR)/usage-bar-monitor.service
	rm -f $(SYSTEMD_USER_DIR)/usage-bar-gui.service
	rm -f $(BINDIR)/$(TARGET)
	rm -f $(BINDIR)/usage-bar-monitor
	systemctl --user daemon-reload

.PHONY: all clean install uninstall
