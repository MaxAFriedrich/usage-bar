CC = gcc
CFLAGS = -Wall -Wextra -O2 -Isrc
LIBS = -lX11 -lXinerama

TARGET = overspeed_monitor
SRCDIR = src
OBJS = $(SRCDIR)/main.o $(SRCDIR)/window.o $(SRCDIR)/socket.o

PREFIX ?= $(HOME)/.local
BINDIR = $(PREFIX)/bin
SHAREDIR = $(PREFIX)/share/usage-bar
SYSCONFDIR ?= /etc/usage-bar
SYSTEMD_USER_DIR = $(HOME)/.config/systemd/user

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $(TARGET) $(OBJS) $(LIBS)

$(SRCDIR)/%.o: $(SRCDIR)/%.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(TARGET) $(SRCDIR)/*.o

install: all
	# Install binaries
	install -d $(BINDIR)
	install -m 755 $(TARGET) $(BINDIR)/
	install -m 755 usage-bar-monitor $(BINDIR)/
	install -m 755 pause.py $(BINDIR)/usage-bar-pause

	# Install Python source files
	install -d $(SHAREDIR)/python-src
	install -m 644 python-src/*.py $(SHAREDIR)/python-src/

	# Install default config to user directory
	install -d $(HOME)/.config/usage-bar
	if [ ! -f $(HOME)/.config/usage-bar/config.yml ]; then \
		install -m 644 config.yml $(HOME)/.config/usage-bar/; \
		echo "Installed config to $(HOME)/.config/usage-bar/config.yml"; \
	else \
		echo "Config already exists at $(HOME)/.config/usage-bar/config.yml (not overwriting)"; \
	fi

	# Install systemd user services
	install -d $(SYSTEMD_USER_DIR)
	sed 's|@BINDIR@|$(BINDIR)|g' systemd/usage-bar-monitor.service > $(SYSTEMD_USER_DIR)/usage-bar-monitor.service
	sed 's|@BINDIR@|$(BINDIR)|g' systemd/usage-bar-gui.service > $(SYSTEMD_USER_DIR)/usage-bar-gui.service
	systemctl --user daemon-reload

	@echo ""
	@echo "Installation complete!"
	@echo "Config location: $(HOME)/.config/usage-bar/config.yml"
	@echo ""
	@echo "To enable and start services:"
	@echo "  systemctl --user enable --now usage-bar-monitor.service"
	@echo "  systemctl --user enable --now usage-bar-gui.service"

install-system-config:
	# Install system-wide default config (requires root)
	install -d $(SYSCONFDIR)
	install -m 644 config.yml $(SYSCONFDIR)/

uninstall:
	systemctl --user stop usage-bar-monitor.service usage-bar-gui.service 2>/dev/null || true
	systemctl --user disable usage-bar-monitor.service usage-bar-gui.service 2>/dev/null || true
	rm -f $(SYSTEMD_USER_DIR)/usage-bar-monitor.service
	rm -f $(SYSTEMD_USER_DIR)/usage-bar-gui.service
	rm -f $(BINDIR)/$(TARGET)
	rm -f $(BINDIR)/usage-bar-monitor
	rm -f $(BINDIR)/usage-bar-pause
	rm -rf $(SHAREDIR)
	systemctl --user daemon-reload
	@echo ""
	@echo "Uninstalled. User config remains at $(HOME)/.config/usage-bar/"
	@echo "To remove config: rm -rf $(HOME)/.config/usage-bar/"

.PHONY: all clean install install-system-config uninstall
