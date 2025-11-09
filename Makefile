CC = gcc
CFLAGS = -Wall -Wextra -O2
LIBS = -lX11 -lXinerama

TARGET = overspeed_monitor
SRC = overspeed_monitor.c

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC) $(LIBS)

clean:
	rm -f $(TARGET)

.PHONY: all clean
