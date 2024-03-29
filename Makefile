#!/usr/bin/make -f


# Main directory from where everything else will be referenced to
MAIN_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

# Where to save time information about the execution of the tasks
export REPORT_TIME_LOG := $(MAIN_DIR)/time_report.log

# Save time information about the execution of the tasks
SHELL=$(MAIN_DIR)/scripts/report_time.sh

LIBRARY=libguesser
PROGRAM=guesser

all: $(LIBRARY).a $(LIBRARY).so $(PROGRAM)

MAJOR=0
MINOR=1

MAPSDIR=./maps

LIB_SOURCES = guesser.c crc32.c utils.c
PRG_SOURCES = main.c

SHARED_OBJS = $(LIB_SOURCES:.c=.shared.o)
STATIC_OBJS = $(LIB_SOURCES:.c=.static.o)

EXTRA_CFLAGS= -DMAPSDIR=\"$(MAPSDIR)\" -DVERSION=\"0.4\"
STATIC_CFLAGS= -O2 -g -Wall -I. $(EXTRA_CFLAGS)
SHARED_CFLAGS= $(STATIC_CFLAGS) -fPIC

LDFLAGS= -Wl,-z,defs -Wl,--as-needed -Wl,--no-undefined
EXTRA_LDFLAGS=

LIB_LIBS= -lm
PRG_LIBS= -lm -L. -lguesser

$(PROGRAM): $(PRG_SOURCES:.c=.static.o) $(LIBRARY).so $(LIBRARY).a
	g++ -o $@ $+ $(PRG_LIBS) ##BIN: $@##

$(LIBRARY).so.$(MAJOR).$(MINOR): $(SHARED_OBJS)
	g++ $(LDFLAGS) $(EXTRA_LDFLAGS) -shared \
		-Wl,-soname,$(LIBRARY).so.$(MAJOR) \
		-o $(LIBRARY).so.$(MAJOR).$(MINOR) \
		$+ -o $@ $(LIB_LIBS) ##$@##

$(LIBRARY).so: $(LIBRARY).so.$(MAJOR).$(MINOR)
	rm -f $@.$(MAJOR)
	ln -s $@.$(MAJOR).$(MINOR) $@.$(MAJOR)
	rm -f $@
	ln -s $@.$(MAJOR) $@

$(LIBRARY).a: $(STATIC_OBJS)
	ar crD $@ $+ ##$@##

%.shared.o: %.cpp
	g++ -o $@ -c $+ $(SHARED_CFLAGS) ##$@##

%.shared.o: %.c
	gcc -o $@ -c $+ $(SHARED_CFLAGS) ##$@##

%.so : %.o
	g++ $(LDFLAGS) $(EXTRA_LDFLAGS) -shared $^ -o $@ ##$@##

%.static.o: %.cpp
	g++ -o $@ -c $+ $(STATIC_CFLAGS) ##$@##

%.static.o: %.c
	gcc -o $@ -c $+ $(STATIC_CFLAGS) ##$@##

clean:
	rm -vf "$(MAIN_DIR)/time_report.log" \
		$(SHARED_OBJS) \
		$(STATIC_OBJS) \
		main.static.o \
		$(PROGRAM) \
		*.so *.so* *.a *~ ##Remove Files##

install: $(LIBRARY).a $(LIBRARY).so $(PROGRAM)
	mkdir -p "$(DESTDIR)/usr/lib/"
	cp -a *.a "$(DESTDIR)/usr/lib/"
	cp -a *.so* "$(DESTDIR)/usr/lib/"
	mkdir -p "$(DESTDIR)/usr/include/"
	cp guesser.h "$(DESTDIR)/usr/include/"
	mkdir -p "$(DESTDIR)/usr/bin/"
	cp guesser "$(DESTDIR)/usr/bin/"
